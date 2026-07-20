import pandas as pd
import numpy as np
import re
import io
from datetime import datetime, timezone
from title_generator import (
    build_seo_title, build_gmc_title,
    is_bilstein, get_bilstein_shocks, get_generation_bilstein,
    build_bilstein_seo_title, build_bilstein_gmc_title,
)
from utils import clean_str, build_lift_range, extract_height_str_from_sku


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
    "Metafield: custom.color [list.single_line_text_field]",
    "Metafield: title_tag [string]",
    "Variant Metafield: custom.gmc_title [single_line_text_field]",
    "Variant Metafield: custom.in_the_box [multi_line_text_field]",
    "Variant Metafield: custom.lift_range [single_line_text_field]",
    "Variant Metafield: custom.shock_position [single_line_text_field]",
    "Variant Metafield: custom.shipping_ome_bilstein [single_line_text_field]",
    "Variant Metafield: custom.shipping_dobinsons [single_line_text_field]",
]

COLOR_COL_CANDIDATES = [
    "Color", "Colour", "color", "colour",
]

PART_SKU_COL_CANDIDATES = [
    "Part Sku", "PartSku", "Part SKU", "part_sku", "Part Number", "PartNumber", "partsku",
]

POSITION_COL_CANDIDATES = [
    "Position", "position", "Pos", "pos",
]

TYPE_COL_CANDIDATES = [
    "Type", "Part Type", "PartType", "part_type", "parttype",
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
        cl = str(c).lower().strip().replace(" ", "").replace("_", "")
        for cand in candidates:
            cand_clean = cand.lower().strip().replace(" ", "").replace("_", "")
            if cand_clean in cl or cl in cand_clean:
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


def normalize_lift_value(val):
    if pd.isna(val):
        return ""
    if isinstance(val, datetime):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", "n/a", "", "nat"):
        return ""
    
    # Si contiene un guión, es un rango - preservarlo tal cual
    if "-" in s:
        # Limpiar texto adicional pero preservar el rango
        s = s.replace(" inches", "").replace(" inch", "").strip()
        return s
    
    # Intentar convertir directamente a número
    try:
        num = float(s)
        if num == int(num):
            return str(int(num))
        return str(num)
    except:
        pass
    
    # Si no es un número puro, extraer el número del texto
    match = re.search(r'(\d+\.?\d*)', s)
    if match:
        num = float(match.group(1))
        if num == int(num):
            return str(int(num))
        return str(num)
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


def build_title(brand, shock_name, lift_range, model, year):
    if "bilstein" in brand.lower():
        marca = "Bilstein B8"
    else:
        marca = brand
    
    shock = shock_name if shock_name else ""
    
    lift_clean = lift_range if lift_range else ""
    
    model_clean = model
    year_abbr = abbreviate_year(year) if year else ""
    
    parts = [p for p in [marca, shock, lift_clean, "Lift Kit", model_clean, f"({year_abbr})"] if p]
    return " ".join(parts)


def build_handle(title, trim="", drive="", assembled=False):
    """
    Genera el handle (URL slug) del producto.
    Si se proporciona un trim, drive, o si es assembled, se agrega al final del handle
    para diferenciar productos (ej: V8, KDSS, 4WD, 2WD, -ass).
    """
    handle = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    if trim and trim.strip():
        trim_slug = re.sub(r'[^a-z0-9]+', '-', trim.lower()).strip('-')
        if trim_slug:
            handle = f"{handle}-{trim_slug}"
    if drive and drive.strip():
        drive_slug = re.sub(r'[^a-z0-9]+', '-', drive.lower()).strip('-')
        if drive_slug:
            handle = f"{handle}-{drive_slug}"
    if assembled:
        handle = f"{handle}-ass"
    return handle


def sort_variants(vars_df):
    def sort_key(row):
        lift = clean_str(row.get("_lift_val", "")).replace(" inches", "").replace(" inch", "")
        lift_num = 0
        if lift:
            # Extraer el primer numero del string para soportar rangos como "2-2.5" o "4-6"
            m = re.search(r'(\d+\.?\d*)', lift)
            if m:
                try:
                    lift_num = float(m.group(1))
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
    df.columns = [str(c).strip().replace('\xa0', ' ').replace('\u200b', '').replace('\t', ' ') for c in df.columns]
    df.columns = [re.sub(r'\s+', ' ', c).strip() for c in df.columns]
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
        "color_col": None,
        "part_sku_col": None,
        "position_col": None,
        "type_col": None,
        "id_col": None,
        "qty_col": None,
        "gen_col": None,
        "engine_col": None,
        "drive_col": None,
        "trim_col": None,
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

    color_col = _find_column(df, COLOR_COL_CANDIDATES)
    info["color_col"] = color_col

    part_sku_col = _find_column(df, PART_SKU_COL_CANDIDATES)
    info["part_sku_col"] = part_sku_col

    position_col = _find_column(df, POSITION_COL_CANDIDATES)
    info["position_col"] = position_col

    type_col = _find_column(df, TYPE_COL_CANDIDATES)
    info["type_col"] = type_col

    # Detectar columnas para SEO/GMC titles
    if "Gen" in df.columns:
        info["gen_col"] = "Gen"
    if "Engine" in df.columns:
        info["engine_col"] = "Engine"
    if "Drive" in df.columns:
        info["drive_col"] = "Drive"
    if "Trim" in df.columns:
        info["trim_col"] = "Trim"
    if "ID" in df.columns:
        info["id_col"] = "ID"

    if shock_col:
        info["shocks"] = sorted([str(s) for s in df[shock_col].dropna().unique().tolist()])

    if "Qty Customer" in df.columns and df["Qty Customer"].notna().any():
        info["qty_col"] = "Qty Customer"
    elif "Qty" in df.columns:
        info["qty_col"] = "Qty"

    for c in ["Make", "Model", "Year", "Brand", "Gen", "Engine", "Drive", "Trim", "Shock"]:
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


def build_in_the_box(vdf_for_sku, qty_col, position_col=None, type_col=None, part_sku_col=None, is_ome=False):
    # Seleccionar columnas necesarias
    cols_needed = ["Part Name", qty_col]
    if position_col and position_col in vdf_for_sku.columns:
        cols_needed.append(position_col)
    if type_col and type_col in vdf_for_sku.columns:
        cols_needed.append(type_col)
    if part_sku_col and part_sku_col in vdf_for_sku.columns:
        cols_needed.append(part_sku_col)
    
    parts = vdf_for_sku[cols_needed].drop_duplicates("Part Name").sort_values("Part Name")
    lines = []
    for _, r in parts.iterrows():
        qv = int(r[qty_col]) if pd.notna(r[qty_col]) and r[qty_col] != 0 else 1
        
        position = clean_str(r.get(position_col, "")) if position_col and position_col in r else ""
        part_type = clean_str(r.get(type_col, "")) if type_col and type_col in r else ""
        
        # Usar Position + Type si están disponibles, sino Part Name
        if position and part_type:
            desc = f"{position} {part_type}"
        elif position:
            desc = position
        elif part_type:
            desc = part_type
        else:
            nm = str(r["Part Name"]).strip() if pd.notna(r["Part Name"]) else "Hardware"
            desc = nm
        
        if part_sku_col and part_sku_col in r and not is_ome:
            sku = clean_str(r.get(part_sku_col, ""))
            if sku:
                lines.append(f"{qv} | {desc} {sku}")
            else:
                lines.append(f"{qv} | {desc}")
        else:
            lines.append(f"{qv} | {desc}")
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

    height_str = ";".join(heights) if heights else ""
    load_str = ";".join(loads) if loads else ""

    return height_str, load_str


def build_matrixify_excel(df, tags="Full Lift Kit, Liftkit", status="Draft",
                          product_type="Lift Kits", lift_col=None, shock_col=None,
                          pin_position_col=None, rear_lift_col=None, color_col=None,
                          part_sku_col=None, position_col=None, type_col=None,
                          qty_col=None, gen_col=None, engine_col=None, 
                          drive_col=None, trim_col=None, option_value_overrides=None):
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

    if color_col is None:
        color_col = _find_column(df, COLOR_COL_CANDIDATES)

    if part_sku_col is None:
        part_sku_col = _find_column(df, PART_SKU_COL_CANDIDATES)

    if position_col is None:
        position_col = _find_column(df, POSITION_COL_CANDIDATES)

    if type_col is None:
        type_col = _find_column(df, TYPE_COL_CANDIDATES)

    # Detectar columnas para SEO/GMC titles si no se proporcionan
    if gen_col is None and "Gen" in df.columns:
        gen_col = "Gen"
    if engine_col is None and "Engine" in df.columns:
        engine_col = "Engine"
    if drive_col is None and "Drive" in df.columns:
        drive_col = "Drive"
    if trim_col is None and "Trim" in df.columns:
        trim_col = "Trim"

    for c in ["Make", "Model", "Year", "Brand", "Gen", "Engine", "Drive", "Trim"]:
        if c in df.columns:
            df[c] = df[c].apply(clean_str)

    if lift_col and lift_col in df.columns:
        df[lift_col] = df[lift_col].apply(normalize_lift_value)
        # Fallback: si la columna Height quedo vacia O es solo un año (ej: "2026" de datetime),
        # intentar extraer la altura del Parent Sku (patron -XXXX-{altura}LEV$).
        # Un año de 4 digitos NO es un height valido, debe disparar el fallback.
        if "Parent Sku" in df.columns:
            empty_or_year_mask = df[lift_col].apply(
                lambda x: not clean_str(x) or re.match(r'^\d{4}$', clean_str(x)) is not None
            )
            if empty_or_year_mask.any():
                df.loc[empty_or_year_mask, lift_col] = df.loc[empty_or_year_mask, "Parent Sku"].apply(
                    extract_height_str_from_sku
                )

    if shock_col and shock_col in df.columns:
        df[shock_col] = df[shock_col].apply(clean_str)

    # Detectar si el SKU tiene "-ASS" (assembled) - esto crea un producto separado
    if "Parent Sku" in df.columns:
        df["_assembled"] = df["Parent Sku"].astype(str).str.contains("-ASS", na=False).map({True: "ass", False: "_NONE_"})

    has_v = pd.Series([True] * len(df), index=df.index)
    if "Make" in df.columns:
        has_v = has_v & (df["Make"] != "")
    if "Model" in df.columns:
        has_v = has_v & (df["Model"] != "")
    df = df[has_v].copy()

    df["_veh"] = df["Make"] + "|" + df["Model"] + "|" + df["Year"] + "|" + df["Brand"]
    # Para Bilstein, el shock es per-position (Front/Rear), NO se incluye en el agrupamiento
    is_bilstein_group = df["Brand"].astype(str).str.strip().str.lower().eq("bilstein").all() if "Brand" in df.columns else False
    if shock_col and shock_col in df.columns and not is_bilstein_group:
        df["_veh"] = df["_veh"] + "|" + df[shock_col].astype(str)
    if trim_col and trim_col in df.columns:
        # Solo agregar Trim si tiene valor (no vacío/NaN)
        # Si dos variantes tienen diferente Trim, serán productos separados
        df["_veh"] = df["_veh"] + "|" + df[trim_col].apply(clean_str).replace("", "_NONE_")
    if drive_col and drive_col in df.columns:
        # Solo agregar Drive si tiene valor (no vacío/NaN)
        # Si dos variantes tienen diferente Drive, serán productos separados
        df["_veh"] = df["_veh"] + "|" + df[drive_col].apply(clean_str).replace("", "_NONE_")
    # Agregar ASS al agrupamiento - variantes con "-ASS" son productos separados
    if "_assembled" in df.columns:
        df["_veh"] = df["_veh"] + "|" + df["_assembled"]
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

        model = clean_str(first.get("Model", ""))
        year = clean_str(first.get("Year", ""))
        title = build_title(brand, shock_name, lift_range, model, year)
        trim_val_handle = clean_str(first.get(trim_col, "")) if trim_col and trim_col in vdf.columns else ""
        drive_val_handle = clean_str(first.get(drive_col, "")) if drive_col and drive_col in vdf.columns else ""
        # Detectar si el producto es ASS (assembled) basándose en los SKUs
        assembled_val = "_assembled" in vdf.columns and vdf["_assembled"].iloc[0] == "ass"
        handle = build_handle(title, trim=trim_val_handle, drive=drive_val_handle, assembled=assembled_val)
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
        # Agregar columnas para SEO/GMC titles
        if gen_col and gen_col in vdf.columns:
            agg_dict[gen_col] = "first"
        if engine_col and engine_col in vdf.columns:
            agg_dict[engine_col] = "first"
        if drive_col and drive_col in vdf.columns:
            agg_dict[drive_col] = "first"
        if trim_col and trim_col in vdf.columns:
            agg_dict[trim_col] = "first"
        # Agregar Internal Type para detectar Leveling Kit vs Lift Kit por variante
        if "Internal Type" in vdf.columns:
            agg_dict["Internal Type"] = "first"

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

        height_str, load_str = build_product_metafields(vdf, lift_col, qty_col)

        color_str = ""
        if color_col and color_col in vdf.columns and "dobinsons" in vendor.lower():
            colors = [clean_str(c) for c in vdf[color_col].unique() if clean_str(c)]
            color_str = ";".join(sorted(set(colors)))

        # Generar SEO Title (nivel producto)
        gen_val = clean_str(first.get(gen_col, "")) if gen_col and gen_col in vdf.columns else ""
        engine_val = clean_str(first.get(engine_col, "")) if engine_col and engine_col in vdf.columns else ""
        drive_val = clean_str(first.get(drive_col, "")) if drive_col and drive_col in vdf.columns else ""
        trim_val = clean_str(first.get(trim_col, "")) if trim_col and trim_col in vdf.columns else ""
        internal_type_val = clean_str(first.get("Internal Type", "")) if "Internal Type" in vdf.columns else ""
        
        # Detectar marca y rutear a las funciones correctas
        if is_bilstein(brand):
            # Reglas Bilstein: front/rear shocks, Gen = años sin filtrar
            front_shock, rear_shock = get_bilstein_shocks(vdf, shock_col, position_col)
            seo_title = build_bilstein_seo_title(
                vdf, model, year, gen_val, lift_range, internal_type_val,
                front_shock, rear_shock, type_col
            )
        else:
            # Reglas OME (existentes)
            seo_title = build_seo_title(
                vdf, brand, shock_name, lift_range, model, year,
                gen_val, trim_val, assembled=assembled_val
            )

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
            "Metafield: custom.height [list.single_line_text_field]": height_str,
            "Metafield: custom.load [list.single_line_text_field]": load_str,
            "Metafield: custom.color [list.single_line_text_field]": color_str,
            "Metafield: title_tag [string]": seo_title,
        })

        variant_rows = []
        for idx, (_, row) in enumerate(vars_df.iterrows()):
            price = row["Total Price"] if pd.notna(row["Total Price"]) else 0
            lift_val = row["_lift_val"] if row["_lift_val"] else ""
            front_val = row["_front_val"]
            rear_val = row["_rear_val"]

            sku = clean_str(row["Parent Sku"])
            sku_rows = vdf[vdf["Parent Sku"].astype(str).str.strip() == sku]
            is_ome = "old man emu" in vendor.lower() or "ome" in vendor.lower()
            in_the_box = build_in_the_box(sku_rows, qty_col, position_col, type_col, part_sku_col, is_ome)

            height_val = clean_str(row.get(lift_col, "")) if lift_col else ""
            rear_lift_val = clean_str(row.get(rear_lift_col, "")) if rear_lift_col else ""
            lift_range_meta = f"{height_val}|{rear_lift_val}" if height_val or rear_lift_val else ""

            shock_pos = clean_str(row.get(pin_position_col, "")) if pin_position_col else ""

            vendor_lower = vendor.lower()
            shipping_ome = "Shipping OME / Bilstein" if "old man emu" in vendor_lower or "ome" in vendor_lower or "bilstein" in vendor_lower else ""
            shipping_dob = "Shipping Dobinsons" if "dobinsons" in vendor_lower else ""

            # Generar GMC Title (nivel variante)
            gen_val_var = clean_str(row.get(gen_col, "")) if gen_col and gen_col in row else ""
            engine_val_var = clean_str(row.get(engine_col, "")) if engine_col and engine_col in row else ""
            drive_val_var = clean_str(row.get(drive_col, "")) if drive_col and drive_col in row else ""
            trim_val_var = clean_str(row.get(trim_col, "")) if trim_col and trim_col in row else ""
            internal_type_var = clean_str(row.get("Internal Type", "")) if "Internal Type" in row else ""

            # Detectar marca y rutear a las funciones correctas
            if is_bilstein(brand):
                # Reglas Bilstein: front/rear shocks
                front_shock, rear_shock = get_bilstein_shocks(sku_rows, shock_col, position_col)
                gmc_title = build_bilstein_gmc_title(
                    sku_rows, model, year, gen_val_var, lift_val.replace(" inches", ""),
                    internal_type_var, front_shock, rear_shock, type_col
                )
            else:
                # Reglas OME (existentes)
                gmc_title = build_gmc_title(
                    sku_rows, brand, shock_name, lift_val.replace(" inches", ""),
                    model, year, gen_val_var, engine_val_var, drive_val_var,
                    trim_val_var, type_col, internal_type=internal_type_var,
                    assembled=assembled_val
                )

            # Override de Option2/Option3 Value: si el usuario edito el texto de la opcion,
            # usar el override. effective_key = mapped_value si existe, sino el raw value.
            # Asi el lookup en option_value_overrides es consistente con la UI.
            raw_front_load = str(row.get("Front Load", "")).strip() if "Front Load" in row else ""
            raw_rear_load = str(row.get("Rear Load", "")).strip() if "Rear Load" in row else ""
            front_eff = map_option(raw_front_load, FRONT_LOAD_MAP, default="") if raw_front_load else ""
            front_eff = front_eff if front_eff else raw_front_load
            rear_eff = map_option(raw_rear_load, REAR_LOAD_MAP, default="") if raw_rear_load else ""
            rear_eff = rear_eff if rear_eff else raw_rear_load

            final_front = front_val
            final_rear = rear_val
            if option_value_overrides:
                ov_f = option_value_overrides.get("front", {}).get(front_eff)
                if ov_f:
                    final_front = ov_f
                ov_r = option_value_overrides.get("rear", {}).get(rear_eff)
                if ov_r:
                    final_rear = ov_r

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
                "Option2 Value": final_front,
                "Option3 Name": "Select Rear Load (Constant)",
                "Option3 Value": final_rear,
                "Variant Command": "MERGE",
                "Variant Position": idx + 1,
                "Variant SKU": sku,
                "Variant Weight Unit": "lb",
                "Variant Price": price,
                "Variant Taxable": "FALSE",
                "Variant Inventory Tracker": "shopify",
                "Variant Inventory Policy": "continue",
                "Variant Fulfillment Service": "manual",
                "Variant Requires Shipping": "TRUE",
                "Variant Shipping Profile": "General Profile",
                "Variant Inventory Qty": 0,
                "Variant Inventory Adjust": 0,
                "Variant Metafield: custom.in_the_box [multi_line_text_field]": in_the_box,
                "Variant Metafield: custom.lift_range [single_line_text_field]": lift_range_meta,
                "Variant Metafield: custom.shock_position [single_line_text_field]": shock_pos,
                "Variant Metafield: custom.shipping_ome_bilstein [single_line_text_field]": shipping_ome,
                "Variant Metafield: custom.shipping_dobinsons [single_line_text_field]": shipping_dob,
                "Variant Metafield: custom.gmc_title [single_line_text_field]": gmc_title,
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


def build_seo_gmc_only(df, lift_col=None, shock_col=None, gen_col=None,
                       engine_col=None, drive_col=None, trim_col=None, type_col=None,
                       id_col=None, position_col=None):
    """
    Genera un archivo Excel con SOLO los metafields SEO Title y GMC Title
    para actualizar productos existentes en Shopify.
    
    El SEO Title se agrupa por la columna "ID" (1 por producto en Shopify).
    El GMC Title se agrupa por variante.
    
    Retorna: (output_bytes, summary_list, result_dataframe)
    """
    # Detectar columnas si no se proporcionan
    if lift_col is None:
        lift_col = _find_column(df, LIFT_HEIGHT_COL_CANDIDATES)
    if shock_col is None:
        shock_col = _find_column(df, SHOCK_COL_CANDIDATES)
    if gen_col is None and "Gen" in df.columns:
        gen_col = "Gen"
    if engine_col is None and "Engine" in df.columns:
        engine_col = "Engine"
    if drive_col is None and "Drive" in df.columns:
        drive_col = "Drive"
    if trim_col is None and "Trim" in df.columns:
        trim_col = "Trim"
    if type_col is None:
        type_col = _find_column(df, TYPE_COL_CANDIDATES)
    if id_col is None and "ID" in df.columns:
        id_col = "ID"
    
    # Limpiar columnas de vehículo
    for c in ["Make", "Model", "Year", "Brand"]:
        if c in df.columns:
            df[c] = df[c].apply(clean_str)
    
    # Filtrar filas sin Make/Model
    has_v = pd.Series([True] * len(df), index=df.index)
    if "Make" in df.columns:
        has_v = has_v & (df["Make"] != "")
    if "Model" in df.columns:
        has_v = has_v & (df["Model"] != "")
    df = df[has_v].copy()
    
    # Normalizar columna de lift height para evitar errores de tipo mixto
    if lift_col and lift_col in df.columns:
        df[lift_col] = df[lift_col].apply(normalize_lift_value)
    
    # Normalizar columnas que se usarán en groupby para evitar errores de tipo mixto
    if shock_col and shock_col in df.columns:
        df[shock_col] = df[shock_col].apply(clean_str)
    if gen_col and gen_col in df.columns:
        df[gen_col] = df[gen_col].apply(clean_str)
    if engine_col and engine_col in df.columns:
        df[engine_col] = df[engine_col].apply(clean_str)
    if drive_col and drive_col in df.columns:
        df[drive_col] = df[drive_col].apply(clean_str)
    if trim_col and trim_col in df.columns:
        df[trim_col] = df[trim_col].apply(clean_str)
    if "Parent Sku" in df.columns:
        df["Parent Sku"] = df["Parent Sku"].apply(clean_str)
    if "Front Load" in df.columns:
        df["Front Load"] = df["Front Load"].apply(clean_str)
    if "Rear Load" in df.columns:
        df["Rear Load"] = df["Rear Load"].apply(clean_str)
    if "Total Price" in df.columns:
        df["Total Price"] = pd.to_numeric(df["Total Price"], errors='coerce')
    
    # Detectar si el SKU tiene "-ASS" (assembled) - esto crea un producto separado
    if "Parent Sku" in df.columns:
        df["_assembled"] = df["Parent Sku"].astype(str).str.contains("-ASS", na=False).map({True: "ass", False: "_NONE_"})
    
    # Agrupar por vehículo + shock + trim
    df["_veh"] = df["Make"] + "|" + df["Model"] + "|" + df["Year"] + "|" + df["Brand"]
    # Para Bilstein, el shock es per-position (Front/Rear), NO se incluye en el agrupamiento
    is_bilstein_group = df["Brand"].astype(str).str.strip().str.lower().eq("bilstein").all() if "Brand" in df.columns else False
    if shock_col and shock_col in df.columns and not is_bilstein_group:
        df["_veh"] = df["_veh"] + "|" + df[shock_col].astype(str)
    if trim_col and trim_col in df.columns:
        # Solo agregar Trim si tiene valor (no vacío/NaN)
        # Si dos variantes tienen diferente Trim, serán productos separados
        df["_veh"] = df["_veh"] + "|" + df[trim_col].apply(clean_str).replace("", "_NONE_")
    if drive_col and drive_col in df.columns:
        # Solo agregar Drive si tiene valor (no vacío/NaN)
        # Si dos variantes tienen diferente Drive, serán productos separados
        df["_veh"] = df["_veh"] + "|" + df[drive_col].apply(clean_str).replace("", "_NONE_")
    # Agregar ASS al agrupamiento - variantes con "-ASS" son productos separados
    if "_assembled" in df.columns:
        df["_veh"] = df["_veh"] + "|" + df["_assembled"]
    vehicles = sorted(df["_veh"].unique())
    
    all_rows = []
    summary = []
    
    # Determinar si agrupar por ID o por _veh
    if id_col and id_col in df.columns:
        # Agrupar por ID (1 SEO Title por producto en Shopify)
        products = df[id_col].dropna().unique()
        products = [p for p in products if str(p).strip() != ""]
        product_groups = [(p, df[df[id_col] == p].copy()) for p in products]
    else:
        # Fallback: agrupar por _veh (comportamiento anterior)
        product_groups = [(vk, df[df["_veh"] == vk].copy()) for vk in vehicles]
    
    for pk, vdf in product_groups:
        first = vdf.iloc[0]
        brand = clean_str(first.get("Brand", ""))
        shock_name = clean_str(first.get(shock_col, "")) if shock_col else ""
        model = clean_str(first.get("Model", ""))
        year = clean_str(first.get("Year", ""))
        
        # Calcular rango de alturas
        lift_values = []
        if lift_col and lift_col in vdf.columns:
            lift_values = vdf[lift_col].unique().tolist()
        lift_range = build_lift_range(lift_values)
        
        # Generar SEO Title (nivel producto)
        gen_val = clean_str(first.get(gen_col, "")) if gen_col and gen_col in vdf.columns else ""
        engine_val = clean_str(first.get(engine_col, "")) if engine_col and engine_col in vdf.columns else ""
        drive_val = clean_str(first.get(drive_col, "")) if drive_col and drive_col in vdf.columns else ""
        trim_val = clean_str(first.get(trim_col, "")) if trim_col and trim_col in vdf.columns else ""
        internal_type_val = clean_str(first.get("Internal Type", "")) if "Internal Type" in vdf.columns else ""
        # Detectar si el producto es ASS (assembled) basándose en los SKUs
        assembled_val = "_assembled" in vdf.columns and vdf["_assembled"].iloc[0] == "ass"

        # Detectar marca y rutear a las funciones correctas
        if is_bilstein(brand):
            # Reglas Bilstein: front/rear shocks, Gen = años sin filtrar
            front_shock_seo, rear_shock_seo = get_bilstein_shocks(vdf, shock_col, position_col)
            seo_title = build_bilstein_seo_title(
                vdf, model, year, gen_val, lift_range, internal_type_val,
                front_shock_seo, rear_shock_seo, type_col
            )
        else:
            # Reglas OME (existentes)
            seo_title = build_seo_title(
                vdf, brand, shock_name, lift_range, model, year,
                gen_val, trim_val, assembled=assembled_val
            )
        
        # Generar handle (necesario para identificar el producto)
        title = build_title(brand, shock_name, lift_range, model, year)
        trim_val_handle = clean_str(first.get(trim_col, "")) if trim_col and trim_col in vdf.columns else ""
        drive_val_handle = clean_str(first.get(drive_col, "")) if drive_col and drive_col in vdf.columns else ""
        handle = build_handle(title, trim=trim_val_handle, drive=drive_val_handle, assembled=assembled_val)
        
        # Fila de producto con SEO Title
        product_row = {
            "ID": pk,
            "Handle": handle,
            "Command": "UPDATE",
            "Metafield: title_tag [string]": seo_title,
        }
        all_rows.append(product_row)
        
        # Generar GMC Title para cada variante
        group_cols = ["Parent Sku"]
        if lift_col and lift_col in vdf.columns:
            group_cols = [lift_col, "Parent Sku"]
        
        agg_dict = {
            "Total Price": "first",
            "Front Load": "first",
            "Rear Load": "first",
        }
        if gen_col and gen_col in vdf.columns:
            agg_dict[gen_col] = "first"
        if engine_col and engine_col in vdf.columns:
            agg_dict[engine_col] = "first"
        if drive_col and drive_col in vdf.columns:
            agg_dict[drive_col] = "first"
        if trim_col and trim_col in vdf.columns:
            agg_dict[trim_col] = "first"
        # Agregar Internal Type para detectar Leveling Kit vs Lift Kit por variante
        if "Internal Type" in vdf.columns:
            agg_dict["Internal Type"] = "first"
        
        vars_df = vdf.groupby(group_cols, as_index=False).agg(agg_dict)
        
        if lift_col and lift_col in vdf.columns:
            vars_df["_lift_val"] = vars_df[lift_col].apply(
                lambda x: f"{clean_str(x)} inches" if clean_str(x) else ""
            )
        else:
            vars_df["_lift_val"] = vars_df["Parent Sku"].apply(extract_lift_from_sku)
        
        for idx, (_, row) in enumerate(vars_df.iterrows()):
            sku = clean_str(row["Parent Sku"])
            sku_rows = vdf[vdf["Parent Sku"].astype(str).str.strip() == sku]
            
            gen_val_var = clean_str(row.get(gen_col, "")) if gen_col and gen_col in row else ""
            engine_val_var = clean_str(row.get(engine_col, "")) if engine_col and engine_col in row else ""
            drive_val_var = clean_str(row.get(drive_col, "")) if drive_col and drive_col in row else ""
            trim_val_var = clean_str(row.get(trim_col, "")) if trim_col and trim_col in row else ""
            internal_type_var = clean_str(row.get("Internal Type", "")) if "Internal Type" in row else ""

            # Detectar marca y rutear a las funciones correctas
            if is_bilstein(brand):
                # Reglas Bilstein: front/rear shocks
                front_shock_gmc, rear_shock_gmc = get_bilstein_shocks(sku_rows, shock_col, position_col)
                gmc_title = build_bilstein_gmc_title(
                    sku_rows, model, year, gen_val_var, lift_range,
                    internal_type_var, front_shock_gmc, rear_shock_gmc, type_col
                )
            else:
                # Reglas OME (existentes)
                gmc_title = build_gmc_title(
                    sku_rows, brand, shock_name, lift_range,
                    model, year, gen_val_var, engine_val_var, drive_val_var,
                    trim_val_var, type_col, internal_type=internal_type_var,
                    assembled=assembled_val
                )
            
            variant_row = {
                "ID": pk,
                "Handle": handle,
                "Command": "UPDATE",
                "Variant SKU": sku,
                "Variant Metafield: custom.gmc_title [single_line_text_field]": gmc_title,
            }
            all_rows.append(variant_row)
        
        summary.append({
            "product_id": pk if (id_col and id_col in df.columns) else str(pk),
            "handle": handle,
            "seo_title": seo_title,
            "seo_chars": len(seo_title),
            "variants": len(vars_df),
        })
    
    # Crear DataFrame con solo las columnas necesarias
    result_df = pd.DataFrame(all_rows)
    
    # Exportar a Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result_df.to_excel(writer, sheet_name="Products", index=False)
    output.seek(0)
    
    return output, summary, result_df
