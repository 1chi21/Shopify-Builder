import pandas as pd
import numpy as np
import re
import io
from datetime import datetime, timezone


FRONT_LOAD_MAP = {
    "Standard": "Standard (Up to 50 lbs)",
    "Medium": "Medium (50-150 lbs)",
    "Heavy": "Heavy (150-250 lbs)",
    "Heavy Duty": "Heavy (150-250 lbs)",
    "Extra Heavy": "Extra Heavy",
}

REAR_LOAD_MAP = {
    "Standard": "Standard (Up to 200 lbs)",
    "Stock": "Standard (Up to 200 lbs)",
    "Medium": "Medium (225-400 lbs)",
    "Heavy": "Heavy (+400 lbs)",
    "HeavyDuty": "Heavy (+400 lbs)",
    "Extra Heavy": "Extra Heavy",
    "Block": "Block",
    "AddALeaf": "Add-A-Leaf",
}

FRONT_LOAD_ORDER = {
    "Standard (Up to 50 lbs)": 0,
    "Medium (50-150 lbs)": 1,
    "Heavy (150-250 lbs)": 2,
    "Extra Heavy": 3,
    "None - I'll use my own": 99,
}

REAR_LOAD_ORDER = {
    "None - I'll use my own": 0,
    "Standard (Up to 200 lbs)": 1,
    "Medium (225-400 lbs)": 2,
    "Heavy (+400 lbs)": 3,
    "Extra Heavy": 4,
    "Block": 5,
    "Add-A-Leaf": 6,
}

COLS = [
    "Handle", "Command", "Title", "Body HTML", "Vendor", "Type",
    "Tags", "Tags Command", "Status", "Published", "Published At",
    "Published Scope", "Template Suffix", "Gift Card",
    "Option1 Name", "Option1 Value",
    "Option2 Name", "Option2 Value",
    "Option3 Name", "Option3 Value",
    "Variant Command", "Variant Position", "Variant SKU",
    "Variant Barcode", "Variant Image",
    "Variant Weight", "Variant Weight Unit",
    "Variant Price", "Variant Compare At Price", "Variant Cost",
    "Variant Taxable", "Variant Inventory Tracker",
    "Variant Inventory Policy", "Variant Fulfillment Service",
    "Variant Requires Shipping", "Variant Shipping Profile",
    "Variant Inventory Qty", "Variant Inventory Adjust",
    "Metafield: custom.height [list.single_line_text_field]",
    "Metafield: custom.load [list.single_line_text_field]",
    "Variant Metafield: custom.in_the_box [multi_line_text_field]",
    "Variant Metafield: custom.lift_range [single_line_text_field]",
    "Variant Metafield: custom.shock_position [single_line_text_field]",
    "Variant Metafield: custom.shipping_ome_bilstein [single_line_text_field]",
    "Variant Metafield: custom.shipping_dobinsons [single_line_text_field]",
]

LIFT_HEIGHT_COL_CANDIDATES = [
    "Lift Height", "Height", "Lift", "Lift Setting",
    "LiftHeight", "lift_height", "height", "lift",
    "Lift Range", "LiftRange", "lift_range",
]

SHOCK_COL_CANDIDATES = [
    "Shock", "Shock Type", "ShockType", "shock", "shock_type",
]

PIN_POSITION_COL_CANDIDATES = [
    "Pin Position for Install", "Pin Position", "pin_position",
]

REAR_LIFT_COL_CANDIDATES = [
    "Rear Lift", "RearLift", "rear_lift",
]


def _find_column(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        cl = str(c).lower().strip()
        for cand in candidates:
            if cand.lower() in cl:
                return c
    return None


def map_option(val, mapping, default="None - I'll use my own"):
    if pd.isna(val) or str(val).strip().upper() in ("N/A", "", "NONE"):
        return default
    return mapping.get(str(val).strip(), default)


def now_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %z").strip()


def blank_row():
    return {c: "" for c in COLS}


def clean_str(val):
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", "n/a", ""):
        return ""
    return s


def normalize_lift_value(val):
    if pd.isna(val):
        return ""
    if isinstance(val, datetime):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", "n/a", "", "nat"):
        return ""
    try:
        num = float(s)
        if num == int(num):
            return str(int(num))
        return str(num)
    except:
        return s


def extract_lift_from_sku(sku):
    sku = str(sku).upper()
    m = re.search(r'(\d+\.?\d*)\s*(?:STC|MED|HVY|STOCK)', sku)
    if m:
        val = float(m.group(1))
        if val == int(val):
            return f"{int(val)} inches"
        return f"{val} inches"
    return None


def build_lift_range(lift_values):
    nums = []
    for v in lift_values:
        v = clean_str(v)
        if not v:
            continue
        v = v.replace(" inches", "").replace(" inch", "").strip()
        try:
            nums.append(float(v))
        except:
            pass
    if not nums:
        return ""
    nums = sorted(set(nums))
    min_v = nums[0]
    max_v = nums[-1]
    if min_v == max_v:
        if min_v == int(min_v):
            return f"{int(min_v)} inch"
        return f"{min_v} inch"
    if min_v == int(min_v):
        min_s = str(int(min_v))
    else:
        min_s = str(min_v)
    if max_v == int(max_v):
        max_s = str(int(max_v))
    else:
        max_s = str(max_v)
    return f"{min_s}-{max_s} inch"


def build_body_html(parts_df, qty_col):
    up = parts_df[["Part Name", qty_col]].drop_duplicates("Part Name").sort_values("Part Name")
    rows = ""
    for _, r in up.iterrows():
        nm = str(r["Part Name"]).strip() if pd.notna(r["Part Name"]) else "Hardware"
        qv = int(r[qty_col]) if pd.notna(r[qty_col]) and r[qty_col] != 0 else 1
        rows += f'<tr><td><p>{nm}</p></td><td><p style="text-align:center;">{qv}</p></td></tr>'
    return f"<table><tbody><tr><td><strong>Item</strong></td><td><strong>Qty</strong></td></tr>{rows}</tbody></table>"


def abbreviate_year(year_str):
    parts = re.findall(r'\d{4}', str(year_str))
    if not parts:
        return year_str
    short = [p[2:] for p in parts]
    if len(short) == 1:
        return short[0]
    return f"{short[0]}-{short[-1]}"


def build_title(first_row, brand, shock_name="", lift_range=""):
    make = clean_str(first_row.get("Make", ""))
    model = clean_str(first_row.get("Model", ""))
    year = clean_str(first_row.get("Year", ""))
    pts = [brand]
    if shock_name:
        pts.append(shock_name)
    pts.append("Lift Kit")
    if make and model:
        pts.append(f"for {make} {model}")
    if year:
        pts.append(f"({abbreviate_year(year)})")
    if lift_range:
        pts.append(f"- {lift_range}")
    return " ".join(pts)


def build_handle(title):
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')


def sort_variants(vars_df):
    def sort_key(row):
        lift = clean_str(row.get("_lift_val", "")).replace(" inches", "").replace(" inch", "")
        try:
            lift_num = float(lift) if lift else 0
        except:
            lift_num = 0
        front_order = FRONT_LOAD_ORDER.get(row["_front_val"], 99)
        rear_order = REAR_LOAD_ORDER.get(row["_rear_val"], 99)
        return (lift_num, front_order, rear_order)

    rows = vars_df.to_dict("records")
    rows.sort(key=sort_key)
    return pd.DataFrame(rows)


def parse_input(filepath_or_buffer):
    df = pd.read_excel(filepath_or_buffer, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def analyze_input(df):
    info = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "vendors": [],
        "vehicles": [],
        "shocks": [],
        "lift_col": None,
        "shock_col": None,
        "pin_position_col": None,
        "rear_lift_col": None,
        "qty_col": None,
    }

    if "Brand" in df.columns:
        info["vendors"] = sorted(df["Brand"].dropna().unique().tolist())

    lift_col = _find_column(df, LIFT_HEIGHT_COL_CANDIDATES)
    info["lift_col"] = lift_col

    shock_col = _find_column(df, SHOCK_COL_CANDIDATES)
    info["shock_col"] = shock_col

    pin_position_col = _find_column(df, PIN_POSITION_COL_CANDIDATES)
    info["pin_position_col"] = pin_position_col

    rear_lift_col = _find_column(df, REAR_LIFT_COL_CANDIDATES)
    info["rear_lift_col"] = rear_lift_col

    if shock_col:
        info["shocks"] = sorted([str(s) for s in df[shock_col].dropna().unique().tolist()])

    if "Qty Customer" in df.columns and df["Qty Customer"].notna().any():
        info["qty_col"] = "Qty Customer"
    elif "Qty" in df.columns:
        info["qty_col"] = "Qty"

    for c in ["Make", "Model", "Year", "Brand"]:
        if c in df.columns:
            df[c] = df[c].apply(clean_str)

    has_v = pd.Series([True] * len(df), index=df.index)
    if "Make" in df.columns:
        has_v = has_v & (df["Make"] != "")
    if "Model" in df.columns:
        has_v = has_v & (df["Model"] != "")
    veh_df = df[has_v]

    veh_keys = []
    if all(c in veh_df.columns for c in ["Make", "Model", "Year"]):
        veh_keys = veh_df.apply(
            lambda r: f"{r['Make']}|{r['Model']}|{r['Year']}", axis=1
        ).unique().tolist()
    info["vehicles"] = sorted(veh_keys)
    info["vehicles_without_data"] = len(df) - len(veh_df)

    return info


def build_in_the_box(vdf_for_sku, qty_col):
    parts = vdf_for_sku[["Part Name", qty_col]].drop_duplicates("Part Name").sort_values("Part Name")
    lines = []
    for _, r in parts.iterrows():
        nm = str(r["Part Name"]).strip() if pd.notna(r["Part Name"]) else "Hardware"
        qv = int(r[qty_col]) if pd.notna(r[qty_col]) and r[qty_col] != 0 else 1
        lines.append(f"{qv} | {nm}")
    return " | ".join(lines)


def build_product_metafields(vdf, lift_col, qty_col):
    heights = []
    if lift_col and lift_col in vdf.columns:
        for v in vdf[lift_col].unique():
            v = clean_str(v)
            if v:
                heights.append(f"{v} inch")
    heights = sorted(set(heights), key=lambda x: float(x.replace(" inch", "")) if x.replace(" inch", "").replace(".", "").isdigit() else 0)

    loads = []
    if "Front Load" in vdf.columns:
        for v in vdf["Front Load"].unique():
            v = clean_str(v)
            if v and v not in ("N/A", "NONE"):
                loads.append(v)
    loads = sorted(set(loads))

    import json
    height_json = json.dumps(heights) if heights else ""
    load_json = json.dumps(loads) if loads else ""

    return height_json, load_json


def build_matrixify_excel(df, tags="Full Lift Kit, Liftkit", status="Draft",
                          product_type="Lift Kits", lift_col=None, shock_col=None,
                          pin_position_col=None, rear_lift_col=None, qty_col=None):
    if qty_col is None:
        if "Qty Customer" in df.columns and df["Qty Customer"].notna().any():
            qty_col = "Qty Customer"
        elif "Qty" in df.columns:
            qty_col = "Qty"
        else:
            raise ValueError("No se encontro columna Qty o Qty Customer")

    if lift_col is None:
        lift_col = _find_column(df, LIFT_HEIGHT_COL_CANDIDATES)

    if shock_col is None:
        shock_col = _find_column(df, SHOCK_COL_CANDIDATES)

    if pin_position_col is None:
        pin_position_col = _find_column(df, PIN_POSITION_COL_CANDIDATES)

    if rear_lift_col is None:
        rear_lift_col = _find_column(df, REAR_LIFT_COL_CANDIDATES)

    for c in ["Make", "Model", "Year", "Brand"]:
        if c in df.columns:
            df[c] = df[c].apply(clean_str)

    if lift_col and lift_col in df.columns:
        df[lift_col] = df[lift_col].apply(normalize_lift_value)

    if shock_col and shock_col in df.columns:
        df[shock_col] = df[shock_col].apply(clean_str)

    has_v = pd.Series([True] * len(df), index=df.index)
    if "Make" in df.columns:
        has_v = has_v & (df["Make"] != "")
    if "Model" in df.columns:
        has_v = has_v & (df["Model"] != "")
    df = df[has_v].copy()

    veh_parts = [df["Make"], df["Model"], df["Year"], df["Brand"]]
    if shock_col and shock_col in df.columns:
        veh_parts.append(df[shock_col])
    df["_veh"] = "|".join(veh_parts)
    vehicles = sorted(df["_veh"].unique())

    all_product_rows = []
    summary = []

    for vk in vehicles:
        vdf = df[df["_veh"] == vk].copy()
        first = vdf.iloc[0]
        brand = clean_str(first.get("Brand", ""))
        vendor = brand if brand else "Unknown"
        shock_name = clean_str(first.get(shock_col, "")) if shock_col else ""

        lift_values = []
        if lift_col and lift_col in vdf.columns:
            lift_values = vdf[lift_col].unique().tolist()
        lift_range = build_lift_range(lift_values)

        title = build_title(first, brand, shock_name=shock_name, lift_range=lift_range)
        handle = build_handle(title)
        pub_at = now_timestamp()
        body_html = build_body_html(vdf, qty_col)

        group_cols = ["Parent Sku"]
        if lift_col and lift_col in vdf.columns:
            group_cols = [lift_col, "Parent Sku"]

        agg_dict = {
            "Total Price": "first",
            "Front Load": "first",
            "Rear Load": "first",
        }
        if pin_position_col and pin_position_col in vdf.columns:
            agg_dict[pin_position_col] = "first"
        if rear_lift_col and rear_lift_col in vdf.columns:
            agg_dict[rear_lift_col] = "first"

        vars_df = vdf.groupby(group_cols, as_index=False).agg(agg_dict)

        if lift_col and lift_col in vdf.columns:
            vars_df["_lift_val"] = vars_df[lift_col].apply(
                lambda x: f"{clean_str(x)} inches" if clean_str(x) else ""
            )
        else:
            vars_df["_lift_val"] = vars_df["Parent Sku"].apply(extract_lift_from_sku)

        vars_df["_front_val"] = vars_df["Front Load"].apply(
            lambda x: map_option(x, FRONT_LOAD_MAP)
        )
        vars_df["_rear_val"] = vars_df["Rear Load"].apply(
            lambda x: map_option(x, REAR_LOAD_MAP)
        )

        vars_df["_opt_key"] = (
            vars_df["_lift_val"] + "|" +
            vars_df["_front_val"] + "|" +
            vars_df["_rear_val"]
        )
        vars_df = vars_df.drop_duplicates(subset=["_opt_key"], keep="first")

        vars_df = sort_variants(vars_df)

        height_json, load_json = build_product_metafields(vdf, lift_col, qty_col)

        product_row = blank_row()
        product_row.update({
            "Handle": handle,
            "Command": "NEW",
            "Title": title,
            "Body HTML": body_html,
            "Vendor": vendor,
            "Type": product_type,
            "Tags": tags,
            "Tags Command": "MERGE",
            "Status": status,
            "Published": "FALSE",
            "Published At": pub_at,
            "Published Scope": "global",
            "Gift Card": "FALSE",
            "Metafield: custom.height [list.single_line_text_field]": height_json,
            "Metafield: custom.load [list.single_line_text_field]": load_json,
        })

        variant_rows = []
        for idx, (_, row) in enumerate(vars_df.iterrows()):
            price = row["Total Price"] if pd.notna(row["Total Price"]) else 0
            lift_val = row["_lift_val"] if row["_lift_val"] else ""
            front_val = row["_front_val"]
            rear_val = row["_rear_val"]

            sku = clean_str(row["Parent Sku"])
            sku_rows = vdf[vdf["Parent Sku"].astype(str).str.strip() == sku]
            in_the_box = build_in_the_box(sku_rows, qty_col)

            height_val = clean_str(row.get(lift_col, "")) if lift_col else ""
            rear_lift_val = clean_str(row.get(rear_lift_col, "")) if rear_lift_col else ""
            lift_range_meta = f"{height_val}|{rear_lift_val}" if height_val or rear_lift_val else ""

            shock_pos = clean_str(row.get(pin_position_col, "")) if pin_position_col else ""

            vendor_lower = vendor.lower()
            shipping_ome = "Shipping OME / Bilstein" if "old man emu" in vendor_lower or "ome" in vendor_lower or "bilstein" in vendor_lower else ""
            shipping_dob = "Shipping Dobinsons" if "dobinsons" in vendor_lower else ""

            vr = blank_row()
            vr.update({
                "Handle": handle,
                "Command": "NEW",
                "Title": title,
                "Vendor": vendor,
                "Type": product_type,
                "Tags": tags,
                "Tags Command": "MERGE",
                "Status": status,
                "Published": "FALSE",
                "Published At": pub_at,
                "Published Scope": "global",
                "Gift Card": "FALSE",
                "Option1 Name": "Select Desired Lift Setting",
                "Option1 Value": lift_val,
                "Option2 Name": "Select Front Load (Constant)",
                "Option2 Value": front_val,
                "Option3 Name": "Select Rear Load (Constant)",
                "Option3 Value": rear_val,
                "Variant Command": "MERGE",
                "Variant Position": idx + 1,
                "Variant SKU": sku,
                "Variant Weight Unit": "lb",
                "Variant Price": price,
                "Variant Taxable": "FALSE",
                "Variant Inventory Tracker": "shopify",
                "Variant Inventory Policy": "deny",
                "Variant Fulfillment Service": "manual",
                "Variant Requires Shipping": "FALSE",
                "Variant Shipping Profile": "General Profile",
                "Variant Inventory Qty": 0,
                "Variant Inventory Adjust": 0,
                "Variant Metafield: custom.in_the_box [multi_line_text_field]": in_the_box,
                "Variant Metafield: custom.lift_range [single_line_text_field]": lift_range_meta,
                "Variant Metafield: custom.shock_position [single_line_text_field]": shock_pos,
                "Variant Metafield: custom.shipping_ome_bilstein [single_line_text_field]": shipping_ome,
                "Variant Metafield: custom.shipping_dobinsons [single_line_text_field]": shipping_dob,
            })
            variant_rows.append(vr)

        all_rows_for_product = [product_row] + variant_rows
        for r in all_rows_for_product:
            all_product_rows.append([r[c] for c in COLS])

        summary.append({
            "vehicle": vk.replace("|", " "),
            "handle": handle,
            "title": title,
            "vendor": vendor,
            "shock": shock_name,
            "lift_range": lift_range,
            "variants": len(variant_rows),
        })

    result_df = pd.DataFrame(all_product_rows, columns=COLS)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result_df.to_excel(writer, sheet_name="Products", index=False)
    output.seek(0)

    return output, summary, result_df
