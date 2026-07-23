"""
Funciones para generar SEO Title y GMC Title según reglas de Carlos
"""
import re
from datetime import datetime
import pandas as pd
from title_rules import (
    SHOCK_ABBREVIATIONS,
    SHOCK_TECHNOLOGY,
    GENERATION_MAP,
    GMC_TITLE_MAX_LENGTH,
    GMC_ALTERNATIVE_TEXT,
    ASSEMBLY_TEXT,
    BILSTEIN_SHOCK_TECH,
)
from utils import clean_str, build_lift_range


def get_generation(gen_value):
    """
    Convierte el valor de Gen a formato legible para título
    Ejemplo: "5thGen" -> "5th Gen"

    Retorna string vacío si el valor parece un año o rango de años (ej: "2018",
    "2010-2016", "2010-16") o un datetime (ej: "2018-07-01..."), para evitar
    duplicar el año en el título.
    """
    if pd.isna(gen_value):
        return ""
    if isinstance(gen_value, datetime):
        return ""
    gen_str = str(gen_value).strip()
    # Si es un string que parece datetime (YYYY-MM-DD...), ignorar
    if re.match(r'^\d{4}-\d{2}-\d{2}', gen_str):
        print(f"[DEBUG get_generation] Gen filtrado (datetime-like): {gen_str!r}")
        return ""
    # Si es un año o rango de años (ej: "2018", "2010-2016", "2010-16", "14-18", "19-ON"), ignorar
    # \d{2,4} acepta tanto 2 digitos (14-18) como 4 digitos (2010-2016)
    # (-\d{2,4}|-ON) acepta "19-ON" (year onwards) y "19-18" (year range)
    if re.match(r'^\d{2,4}(-\d{2,4}|-ON)?$', gen_str):
        print(f"[DEBUG get_generation] Gen filtrado (year/range): {gen_str!r}")
        return ""
    return GENERATION_MAP.get(gen_str, gen_str)


def get_landcruiser_abbreviation(model):
    """
    Extrae la abreviatura de Land Cruiser del modelo.
    Ejemplo: "Land Cruiser 100" -> "LC100", "LandCruiser250" -> "LC250",
              "100 Series Land Cruiser" -> "LC100", "LandCruiser80&105Series" -> "LC80"
    Retorna string vacío si no es un Land Cruiser.
    Se usa para agregar "LC{n}" en el GMC title antes de "Suspension Upgrade".
    """
    if not model:
        return ""
    s = str(model)
    # Pattern 1: numero DESPUES de "Land Cruiser" (ej: "LandCruiser100", "Land Cruiser 100")
    m = re.search(r'[Ll]and\s*[Cc]ruiser\s*(\d+)', s)
    if m:
        return f"LC{m.group(1)}"
    # Pattern 2: numero ANTES de "Land Cruiser" con "Series" (ej: "100 Series Land Cruiser")
    m = re.search(r'(\d+)\s*[Ss]eries?\s*[Ll]and\s*[Cc]ruiser', s)
    if m:
        return f"LC{m.group(1)}"
    return ""


def is_non_rubicon(trim_value):
    """
    Detecta si el trim es "Non Rubicon" (versión por defecto de Rubicon).
    Según Carlos: cuando el trim dice "Non Rubicon" NO lo agregamos al título,
    pero si dice "Rubicon" sí. La Non Rubicon es la versión por defecto.
    """
    if pd.isna(trim_value):
        return False
    return str(trim_value).strip().lower() == "non rubicon"


def count_models_in_string(model_str):
    """
    Cuenta la cantidad de modelos en un string separados por coma, slash, o "y".
    Ejemplo: "Bronco Base, Big Bend, Outer Banks, Wildtrack" -> 4
              "Hilux Vigo" -> 1
              "Bronco Black Diamond, Badlands" -> 2
              "Hilux REVO/ROCCO/SR5" -> 3
    Se usa para detectar default vs caso especial en productos multi-modelo.
    """
    if not model_str or pd.isna(model_str):
        return 0
    s = str(model_str).strip()
    if not s:
        return 0
    # Separar por coma, slash, o " y " (Spanish for "and")
    parts = re.split(r'[,/]|\s+y\s+', s, flags=re.IGNORECASE)
    parts = [p.strip() for p in parts if p.strip()]
    return len(parts)


# Marcas conocidas para extraer del modelo cuando es multi-modelo
# (el input suele tener la marca concatenada: "BroncoBase,BigBend,...")
KNOWN_BRANDS = [
    "LandCruiser", "Land Cruiser", "WranglerJK", "WranglerJL", "WranglerTJ", "WranglerLJ",
    "FJCruiser", "4Runner", "LX450", "LX470", "LX570", "GX470", "GX460",
    "Bronco", "Hilux", "Tacoma", "Tundra", "Patrol", "Defender",
    "Frontier", "Pathfinder", "Ranger", "Fortuner", "Navara",
    "Pajero", "Triton", "Everest", "BT-50", "D-Max", "Mu-X",
    "Discovery", "G-Wagon", "X-Trail",
]


def extract_brand_from_model(model):
    """
    Extrae la marca del modelo (la primera palabra cuando el modelo es multi-modelo).
    Ejemplo: "BroncoBase,BigBend,OuterBanks,Wildtrack" -> "Bronco"
              "HiluxREVO/ROCCO/SR5" -> "Hilux"
              "LandCruiser100Series" -> "LandCruiser"
              "4Runner" -> "4Runner" (no se aplica la logica multi-modelo)
    """
    if not model or pd.isna(model):
        return ""
    s = str(model).strip()
    if not s:
        return ""
    # Buscar la marca mas larga que haga match al inicio
    for brand in sorted(KNOWN_BRANDS, key=len, reverse=True):
        if s.startswith(brand):
            return brand
    return s


def get_model_for_title(model):
    """
    Devuelve el model a usar en el titulo segun la regla multi-modelo de Carlos.
    - Si tiene 3+ modelos: devuelve SOLO la marca (ej: "Bronco")
      (default: producto que cubre mas modelos)
    - Si tiene menos: devuelve el model completo (caso especial)
    
    Ejemplo:
    - "Bronco Base, Big Bend, Outer Banks, Wildtrack" -> "Bronco" (4 modelos)
    - "Bronco Black Diamond, Badlands" -> "Bronco Black Diamond, Badlands" (2 modelos)
    - "Hilux REVO/ROCCO/SR5" -> "Hilux" (3 modelos)
    - "Hilux Vigo" -> "Hilux Vigo" (1 modelo)
    - "LandCruiser100Series" -> "LandCruiser100Series" (1 modelo)
    """
    if not model or pd.isna(model):
        return ""
    s = str(model).strip()
    if not s:
        return ""
    count = count_models_in_string(s)
    if count >= 3:
        return extract_brand_from_model(s)
    return s


def normalize_shock_name(shock_type):
    """
    Normaliza el nombre del shock.
    Si dice "Nitro", lo cambia a "Nitrocharger".
    """
    if pd.isna(shock_type):
        return ""
    shock_str = str(shock_type).strip()
    if shock_str.lower() == "nitro":
        return "Nitrocharger"
    return shock_str


def should_include_engine(engine_value):
    """
    Determina si el engine debe incluirse en el título.
    Si dice "Gas" (case-insensitive), NO se incluye (se sobreentiende).
    Cualquier otro valor SÍ se incluye.
    Retorna True si debe incluirse, False si no.
    """
    if pd.isna(engine_value):
        return False
    engine_str = str(engine_value).strip()
    if engine_str.lower() == "gas":
        return False
    return True


def get_shock_abbreviation(brand, shock_type):
    """
    Obtiene la abreviación de marca para el shock
    Ejemplo: "Old Man Emu" -> "OME"
    """
    if pd.isna(brand):
        return ""
    brand_str = str(brand).strip()
    return SHOCK_ABBREVIATIONS.get(brand_str, brand_str)


def get_shock_technology(shock_type):
    """
    Obtiene la tecnología y arquitectura del shock
    Retorna: (technology, architecture)
    """
    if pd.isna(shock_type):
        return "", ""
    shock_str = str(shock_type).strip()
    tech_info = SHOCK_TECHNOLOGY.get(shock_str, {})
    return tech_info.get("technology", ""), tech_info.get("architecture", "")


def has_leaf_springs(vdf_for_product, type_col):
    """
    Verifica si el producto tiene leaf springs
    Busca en la columna Type si hay valores como "Leaf Spring" o similar
    """
    if not type_col or type_col not in vdf_for_product.columns:
        return False
    
    type_values = vdf_for_product[type_col].dropna().astype(str).str.lower()
    leaf_keywords = ["leaf", "leaf spring", "rear leaf"]
    
    for val in type_values:
        for keyword in leaf_keywords:
            if keyword in val:
                return True
    return False


def determine_kit_type(internal_type_value=None, vdf_for_product=None, type_col=None):
    """
    Determina si el producto es un "Leveling Kit", "Shocks Set Kit" o "Lift Kit"
    basándose en el valor de Internal Type o buscando en el DataFrame.
    Regla Carlos v1.11.11:
    - "Leveling" -> "Leveling Kit"
    - "Shocks Set" -> "Shocks Set Kit"
    - otro -> "Lift Kit"
    """
    # Si se pasa el valor directo de Internal Type, usarlo
    if internal_type_value is not None and not pd.isna(internal_type_value):
        val_lower = str(internal_type_value).lower()
        if "leveling" in val_lower:
            return "Leveling Kit"
        elif "shocks set" in val_lower:
            return "Shocks Set Kit"
        else:
            return "Lift Kit"

    # Si no, buscar en el DataFrame
    if vdf_for_product is None or len(vdf_for_product) == 0:
        return "Lift Kit"

    # Buscar en columnas relevantes
    columns_to_check = ["Type", "Internal Type", "Product Type", "Platform"]
    if type_col:
        columns_to_check.insert(0, type_col)

    for col in columns_to_check:
        if col in vdf_for_product.columns:
            values = vdf_for_product[col].dropna().astype(str).str.lower()
            for val in values:
                if "leveling" in val:
                    return "Leveling Kit"
                elif "shocks set" in val:
                    return "Shocks Set Kit"

    return "Lift Kit"


def build_seo_title(vdf_for_product, brand, shock_type, lift_range, model, year, gen, trim, type_col=None, assembled=False):
    """
    Genera SEO Title según reglas de Carlos
    Formato: MARCA_ABREVIADA SHOCK GENERACIÓN MODELO [TRIM] [LIFT/LEVELING Kit] [w/ Strut Assembly] RANGO_ALTURAS (AÑOS)
    Sin límite de caracteres (nivel producto).
    
    Ejemplo: "OME BP-51 5th Gen 4Runner Lift Kit 2-3" (2010-2024)"
    Ejemplo Leveling: "OME Nitro 3rd Gen 4Runner Leveling Kit 2" (1996-2002)"
    Ejemplo Assembly: "OME BP-51 5th Gen 4Runner Lift Kit w/ Strut Assembly 2-3" (2010-2024)"
    """
    brand_abbr = get_shock_abbreviation(brand, shock_type)
    shock = normalize_shock_name(shock_type)
    generation = get_generation(gen)
    # Regla Carlos multi-modelo: si tiene 3+ modelos usar solo la marca
    model_clean = get_model_for_title(model)
    trim_clean = clean_str(trim) if trim else ""
    
    # Determinar si es Leveling Kit o Lift Kit
    kit_type = determine_kit_type(vdf_for_product=vdf_for_product, type_col=type_col)
    
    # Convertir rango de alturas a formato con comillas
    # Ejemplo: "2-3 inch" -> "2-3""
    lift_formatted = lift_range.replace(" inch", '"') if lift_range else ""
    
    # Formato de años
    year_formatted = f"({year})" if year else ""
    
    # Construir título
    parts = [brand_abbr, shock, generation, model_clean]
    # Regla Carlos: Non Rubicon NO se agrega (es la version por defecto).
    # Solo Rubicon (u otros trims validos) se agregan al titulo.
    if trim_clean and not is_non_rubicon(trim_clean):
        parts.append(trim_clean)
    parts.append(kit_type)
    if assembled:
        parts.append(ASSEMBLY_TEXT)
    parts.extend([lift_formatted, year_formatted])
    
    # Filtrar partes vacías
    parts = [p for p in parts if p]
    
    seo_title = " ".join(parts)
    
    # Sin límite de caracteres para SEO Title
    
    return seo_title


def build_gmc_title(
    vdf_for_variant,
    brand,
    shock_type,
    lift_range,
    model,
    year,
    gen,
    engine,
    drive,
    trim,
    type_col,
    internal_type=None,
    assembled=False,
):
    """
    Genera GMC Title según reglas de Carlos
    Formato: BRAND SHOCK GENERACIÓN MODELO [ENGINE] [DRIVE] [TRIM] [LIFT/LEVELING Kit] [w/ Strut Assembly] RANGO_ALTURAS (AÑOS), 
             MARCA_ABREVIADA TECNOLOGÍA_SHOCK, [SHOCK_ARCHITECTURE], [LEAF_SPRINGS], Suspension Upgrade
    Máximo: 150 caracteres (nivel variante). Para productos Assembly el límite se mantiene pero el
    fallback es más agresivo: primero se quita 'Suspension Upgrade' y como último recurso la tecnología
    del shock (monotube/bypass/twintube) y su arquitectura.
    
    Ejemplo: "Old Man Emu MT64 5th Gen 4Runner Lift Kit 2-3" (2010-2024), OME Monotube Shocks, Suspension Upgrade"
    Ejemplo Leveling: "Old Man Emu Nitro 3rd Gen 4Runner Leveling Kit 2" (1996-2002), OME Twin Tube Shocks, Suspension Upgrade"
    Ejemplo Assembly: "Old Man Emu BP-51 5th Gen 4Runner Lift Kit w/ Strut Assembly 2-3" (2010-2024), OME Bypass Shocks, Suspension Upgrade"
    """
    brand_clean = clean_str(brand) if brand else ""
    shock = normalize_shock_name(shock_type)
    generation = get_generation(gen)
    # Regla Carlos multi-modelo: si tiene 3+ modelos usar solo la marca
    model_clean = get_model_for_title(model)
    engine_clean = clean_str(engine) if engine else ""
    drive_clean = clean_str(drive) if drive else ""
    trim_clean = clean_str(trim) if trim else ""
    
    # Determinar si es Leveling Kit o Lift Kit
    # Primero intentar con el internal_type de la variante, luego con el DataFrame
    kit_type = determine_kit_type(internal_type_value=internal_type, vdf_for_product=vdf_for_variant, type_col=type_col)
    
    # Convertir rango de alturas a formato con comillas
    lift_formatted = lift_range.replace(" inch", '"') if lift_range else ""
    
    # Formato de años
    year_formatted = f"({year})" if year else ""
    
    # Construir primera parte del título
    parts = [brand_clean, shock, generation, model_clean]
    # Solo incluir engine si NO es "Gas" (se sobreentiende)
    if engine_clean and should_include_engine(engine_clean):
        parts.append(engine_clean)
    if drive_clean:
        parts.append(drive_clean)
    # Regla Carlos: Non Rubicon NO se agrega (es la version por defecto).
    # Solo Rubicon (u otros trims validos) se agregan al titulo.
    if trim_clean and not is_non_rubicon(trim_clean):
        parts.append(trim_clean)
    parts.append(kit_type)
    if assembled:
        parts.append(ASSEMBLY_TEXT)
    parts.extend([lift_formatted, year_formatted])
    
    # Filtrar partes vacías
    parts = [p for p in parts if p]
    title_base = " ".join(parts)
    
    # Obtener tecnología y arquitectura del shock
    brand_abbr = get_shock_abbreviation(brand, shock_type)
    technology, architecture = get_shock_technology(shock_type)
    has_leafs = has_leaf_springs(vdf_for_variant, type_col)
    # Regla Carlos: para Land Cruiser, agregar abreviatura "LC{n}" antes de "Suspension Upgrade"
    # Ej: "Land Cruiser 100" -> "LC100", "LandCruiser250" -> "LC250"
    landcruiser_abbr = get_landcruiser_abbreviation(model)
    
    # Helper para reconstruir el título con distintas combinaciones de partes removibles
    def build_full(with_suspension_upgrade, with_tech_description):
        tech_parts = []
        if with_tech_description:
            if brand_abbr and technology:
                tech_parts.append(f"{brand_abbr} {technology}")
            if architecture:
                tech_parts.append(architecture)
        if has_leafs:
            tech_parts.append("Rear Leaf Springs")
        if landcruiser_abbr:
            # Va justo antes de "Suspension Upgrade"
            tech_parts.append(landcruiser_abbr)
        if with_suspension_upgrade:
            tech_parts.append(GMC_ALTERNATIVE_TEXT)
        
        if tech_parts:
            return f"{title_base}, {', '.join(tech_parts)}"
        return title_base
    
    # Construir título completo (con todo)
    gmc_title = build_full(with_suspension_upgrade=True, with_tech_description=True)
    
    # Verificar límite de caracteres
    if len(gmc_title) > GMC_TITLE_MAX_LENGTH:
        # 1) Quitar "Suspension Upgrade" primero
        gmc_title = build_full(with_suspension_upgrade=False, with_tech_description=True)
        
        if len(gmc_title) > GMC_TITLE_MAX_LENGTH:
            if assembled:
                # 2) Para Assembly, como último recurso quitar también la tecnología del shock
                #    y su arquitectura (se mantiene "Rear Leaf Springs" si aplica, no es tech)
                gmc_title = build_full(with_suspension_upgrade=False, with_tech_description=False)
            else:
                # Para no-Assembly, marcar con advertencia
                gmc_title = f"{gmc_title} [EXCEDE {GMC_TITLE_MAX_LENGTH} CHARS]"
    
    return gmc_title


# ============================================================
# BILSTEIN - Reglas específicas para productos Bilstein
# ============================================================

def is_bilstein(brand):
    """
    Verifica si la marca es Bilstein (case-insensitive).
    Segun Carlos: las reglas de titulo dependen de la marca.
    """
    if not brand or pd.isna(brand):
        return False
    return str(brand).strip().lower() == "bilstein"


def get_bilstein_shocks(vdf, shock_col, position_col):
    """
    Extrae los shocks front y rear de un grupo de productos Bilstein.
    Retorna (front_shock, rear_shock).

    Reglas de Carlos:
    - Si el Shock Type tiene "/" (ej: "6112/5100"), el primer numero es front y el segundo es rear
      (caso comun en el archivo "ALL BILSTEIN .xlsx" donde el Shock Type ya viene combinado)
    - Si solo hay un shock (ej: 5100), es siempre el FRONT
    - Si hay dos rows con Position=Front y Position=Rear, usa el Shock Type de cada uno
    """
    if not shock_col or shock_col not in vdf.columns:
        return ("", "")

    # Caso 1: el Shock Type ya viene combinado con "/" (ej: "6112/5100")
    # Todos los rows del grupo tienen el mismo Shock Type combinado
    combined_shocks = vdf[shock_col].dropna().astype(str).unique()
    if len(combined_shocks) >= 1 and any("/" in str(s) for s in combined_shocks):
        # Tomar el primer shock que tenga "/"
        for s in combined_shocks:
            s_str = str(s).strip()
            if "/" in s_str:
                parts = s_str.split("/")
                if len(parts) == 2:
                    return (parts[0].strip(), parts[1].strip())

    # Caso 2: el Shock Type viene separado por Position (Front/Rear)
    if not position_col or position_col not in vdf.columns:
        # Si no hay Position, asumir que el shock del primer row es el front
        return (clean_str(vdf.iloc[0].get(shock_col, "")), "")

    front_rows = vdf[vdf[position_col].astype(str).str.strip().str.lower() == "front"]
    rear_rows = vdf[vdf[position_col].astype(str).str.strip().str.lower() == "rear"]

    front_shock = clean_str(front_rows.iloc[0].get(shock_col, "")) if len(front_rows) > 0 else ""
    rear_shock = clean_str(rear_rows.iloc[0].get(shock_col, "")) if len(rear_rows) > 0 else ""

    return (front_shock, rear_shock)


def format_bilstein_shocks(front_shock, rear_shock):
    """
    Formatea los shocks para mostrar en el titulo Bilstein.
    - Si front y rear son iguales: solo "front" (ej: "5100")
    - Si front y rear son diferentes: "front/rear" (ej: "6112/5160")
    - Si solo hay front: "front"
    - Si solo hay rear: "front" (regla Carlos: uno solo siempre es front)
    """
    if not front_shock and not rear_shock:
        return ""
    if not front_shock:
        # Regla Carlos: uno solo siempre es front
        return rear_shock
    if not rear_shock:
        return front_shock
    if front_shock == rear_shock:
        return front_shock
    return f"{front_shock}/{rear_shock}"


def get_bilstein_shock_tech(front_shock, rear_shock, front_secondary=None, rear_secondary=None):
    """
    Obtiene las tecnologias front y rear de un shock Bilstein.
    Retorna (front_tech, rear_tech).

    Si se proporciona el Secondary Shock Type (ej: "CR/BYP", "DSA/5160"),
    se usa para determinar la tecnologia ESPECIFICA (no la combinada "Tech1 / Tech2").
    Formato del Secondary Shock Type: [CR_o_DSA]/[tech_code]
      - CR = Bilstein B8, DSA = DSA
      - tech_code: 5160=Remote Reservoir, BYP=Bypass, DSA=DSA, REG=Regular
    """
    if front_secondary:
        front_tech = _parse_bilstein_secondary(front_shock, front_secondary, "front")
    else:
        front_tech = BILSTEIN_SHOCK_TECH.get(str(front_shock).strip(), {}).get("front", "")

    if rear_secondary:
        rear_tech = _parse_bilstein_secondary(rear_shock, rear_secondary, "rear")
    else:
        rear_tech = BILSTEIN_SHOCK_TECH.get(str(rear_shock).strip(), {}).get("rear", "")

    return (front_tech, rear_tech)


def _parse_bilstein_secondary(shock, secondary, position):
    """
    Parsea el Secondary Shock Type para obtener la tecnologia especifica con nombres completos.
    secondary: e.g., "CR/5160", "CR/BYP", "CR/SB", "CR/SB+", "DSA/5160"
    position: "front" o "rear"

    Regla Carlos: NO mostrar "Tech1 / Tech2", solo el nombre completo que corresponde.

    Mapeo por shock:
      - 5160: 5160 -> "Remote Reservoir Shocks"
      - 6112: 5160 -> "Adjustable Shocks" (igual que 5100 front)
      - 8112: 5160 -> "Zone Control CR Shocks"
              DSA+  -> "Zone Control CR DSA+ Shocks"
      - 8100: BYP  -> "Bypass Shocks"
              DSA+ -> "Smooth Body DSA+ Shocks"
              SB/REG -> "Smooth Body Shocks"
    """
    if not secondary or "/" not in secondary:
        # Fallback al mapping original (BILSTEIN_SHOCK_TECH)
        return BILSTEIN_SHOCK_TECH.get(str(shock).strip(), {}).get(position, "")

    parts = secondary.split("/")
    if len(parts) != 2:
        return BILSTEIN_SHOCK_TECH.get(str(shock).strip(), {}).get(position, "")

    tech_code = parts[1].strip().upper()
    shock_clean = str(shock).strip()

    # Mapeo actualizado con nombres completos (regla Carlos v1.11.8)
    if shock_clean == "5160":
        # 5160: Remote Reservoir Shocks
        if tech_code == "5160":
            return "Remote Reservoir Shocks"
    elif shock_clean == "6112":
        # 6112: Adjustable Shocks (igual que 5100 front)
        if tech_code == "5160":
            return "Adjustable Shocks"
    elif shock_clean == "8112":
        # 8112: SIEMPRE con "CR" (regla Carlos v1.11.11)
        # - Si es DSA+: "Zone Control CR DSA+ Shocks" (con CR y DSA+)
        # - Si NO es DSA+ (ej: 5160, BYP, REG): "Zone Control CR Shocks" (con CR, sin DSA+)
        if "DSA" in tech_code or "+" in tech_code:
            return "Zone Control CR DSA+ Shocks"
        else:
            return "Zone Control CR Shocks"
    elif shock_clean == "8100":
        # 8100: Smooth Body Shocks, Smooth Body DSA+ Shocks, o Bypass Shocks
        if tech_code == "BYP":
            return "Bypass Shocks"
        elif "DSA" in tech_code or "+" in tech_code:  # SB+ o DSA → DSA+ version
            return "Smooth Body DSA+ Shocks"
        else:  # SB, REG, o cualquier otro
            return "Smooth Body Shocks"

    # Fallback al mapping original
    return BILSTEIN_SHOCK_TECH.get(shock_clean, {}).get(position, "")


def get_generation_bilstein(gen_value):
    """
    DEPRECATED: usar get_generation() en su lugar.
    Se conserva por compatibilidad pero ya no se usa en el flujo principal.
    """
    if pd.isna(gen_value):
        return ""
    return clean_str(gen_value)


def is_bilstein_assembled(vdf):
    """
    Verifica si el producto Bilstein es assembled (tiene -ASS en el SKU).
    Aplica la precaucion de Assembly para cualquier marca.
    """
    if "Parent Sku" in vdf.columns:
        sku = str(vdf.iloc[0].get("Parent Sku", ""))
        if "-ASS" in sku.upper():
            return True
    if "Assembly" in vdf.columns:
        assembly = str(vdf.iloc[0].get("Assembly", "")).strip().upper()
        if assembly in ("ASS", "ASSEMBLED", "YES", "SI", "TRUE", "1"):
            return True
    return False


def build_bilstein_seo_title(vdf, model, year, gen, height, internal_type,
                             front_shock, rear_shock, engine="", drive="", trim="",
                             type_col=None):
    """
    Construye el SEO Title para productos Bilstein.
    Formato: Bilstein {shocks} {model} [engine] [drive] [trim] {gen} {internal_type} {height} ({year})
    Ejemplo: Bilstein 6112/5160 4Runner Gas 4WD 5th Gen Lift Kit 1-3" (2010-2024)
    No se aplica LC100 (Land Cruiser), Non Rubicon, ni multi-modelo.
    Regla Carlos v1.11.11: se incluyen engine, drive, trim cuando existen.
    """
    shocks_str = format_bilstein_shocks(front_shock, rear_shock)

    # Siempre normalizar el internal_type
    kit_type = determine_kit_type(
        internal_type_value=internal_type if internal_type else None,
        vdf_for_product=vdf,
        type_col=type_col
    )

    # Formatear height
    if height:
        h = height.replace(" inch", "").strip()
        height_formatted = f'{h}"'
    else:
        height_formatted = ""
    year_formatted = f"({year})" if year else ""

    # Regla Carlos: si hay generacion la pone, si es año la omite
    gen_clean = get_generation(gen)

    # Engine, drive, trim (orden: engine -> drive -> trim, igual que OME)
    parts = ["Bilstein", shocks_str, model]
    if engine and should_include_engine(engine):
        parts.append(engine)
    if drive:
        parts.append(drive)
    if trim and not is_non_rubicon(trim):
        parts.append(trim)
    parts.extend([gen_clean, kit_type, height_formatted, year_formatted])

    # Assembly: precaucion para cualquier marca
    if is_bilstein_assembled(vdf):
        parts.insert(-2, ASSEMBLY_TEXT)  # Antes de height y year

    parts = [p for p in parts if p]
    return " ".join(parts)


def build_bilstein_gmc_title(vdf, model, year, gen, height, internal_type,
                             front_shock, rear_shock, engine="", drive="", trim="",
                             type_col=None,
                             secondary_shock_type_col=None, position_col=None):
    """
    Construye el GMC Title para productos Bilstein.
    Formato: Bilstein {shocks} {model} {gen} {internal_type} {height} ({year}) {front_tech}, {rear_tech}
    Sin "Suspension Upgrade" (diferente de OME).
    El front tech lleva prefijo "Front", el rear tech no lleva prefijo.
    Si se pasa secondary_shock_type_col, se extrae el Secondary Shock Type del vdf
    (formato: "CR/BYP", "DSA/5160") y se usa para mostrar SOLO la tech especifica
    (no "Bypass / DSA" sino la que corresponde: "Bypass" o "DSA").
    Limite: 150 chars con fallback progresivo: primero rear, luego front, luego [EXCEDE].
    """
    # ============================================================
    # VERSION CHECK v1.11.10 - Si ves este mensaje en los logs
    # de Streamlit Cloud, el codigo nuevo ESTA corriendo
    # ============================================================
    print("=" * 60)
    print("[BILSTEIN VERSION CHECK] v1.11.10 - CODIGO NUEVO CORRIENDO")
    print("[BILSTEIN VERSION CHECK] Si ves esto en los logs, el deploy se hizo OK")
    print(f"[BILSTEIN VERSION CHECK] model={model}, gen={gen}, front_shock={front_shock}, rear_shock={rear_shock}")
    print("=" * 60)
    # ============================================================

    shocks_str = format_bilstein_shocks(front_shock, rear_shock)

    # Siempre normalizar el internal_type
    kit_type = determine_kit_type(
        internal_type_value=internal_type if internal_type else None,
        vdf_for_product=vdf,
        type_col=type_col
    )

    # Formatear height: siempre agregar " al final
    if height:
        h = height.replace(" inch", "").strip()
        height_formatted = f'{h}"'
    else:
        height_formatted = ""
    year_formatted = f"({year})" if year else ""

    # Regla Carlos: si hay generacion la pone, si es año la omite (queda solo el year del final)
    gen_clean = get_generation(gen)

    # Base part
    # Engine, drive, trim (regla Carlos v1.11.11)
    parts = ["Bilstein", shocks_str, model]
    if engine and should_include_engine(engine):
        parts.append(engine)
    if drive:
        parts.append(drive)
    if trim and not is_non_rubicon(trim):
        parts.append(trim)
    parts.extend([gen_clean, kit_type, height_formatted, year_formatted])
    if is_bilstein_assembled(vdf):
        parts.insert(-2, ASSEMBLY_TEXT)
    parts = [p for p in parts if p]
    title_base = " ".join(parts)

    # Extraer Secondary Shock Type del vdf (si la columna existe)
    front_secondary = ""
    rear_secondary = ""
    if secondary_shock_type_col and secondary_shock_type_col in vdf.columns:
        # Detectar columna de Position
        pos_col = position_col
        if not pos_col or pos_col not in vdf.columns:
            for col in ["Position", "position", "Pos", "pos"]:
                if col in vdf.columns:
                    pos_col = col
                    break
        if pos_col and pos_col in vdf.columns:
            front_rows = vdf[vdf[pos_col].astype(str).str.strip().str.lower() == "front"]
            rear_rows = vdf[vdf[pos_col].astype(str).str.strip().str.lower() == "rear"]
            if len(front_rows) > 0:
                front_secondary = clean_str(front_rows.iloc[0].get(secondary_shock_type_col, ""))
            if len(rear_rows) > 0:
                rear_secondary = clean_str(rear_rows.iloc[0].get(secondary_shock_type_col, ""))

    # Tech part (con prefijo "Front" solo en el front)
    front_tech, rear_tech = get_bilstein_shock_tech(
        front_shock, rear_shock, front_secondary, rear_secondary
    )

    # Helper para construir titulo con/sin front/rear tech
    # Regla Carlos v1.11.8 (corregido v1.11.9):
    # - Front tech lleva prefijo "Front"
    # - Rear tech lleva prefijo "Rear"
    # - Entre base y tech: COMA ","
    # - Entre front y rear: AMPERSAND "&"
    def build_with_tech(f_tech, r_tech):
        tech_parts = []
        if f_tech:
            tech_parts.append(f"Front {f_tech}")
        if r_tech:
            tech_parts.append(f"Rear {r_tech}")
        if tech_parts:
            return f"{title_base}, {' & '.join(tech_parts)}"
        return title_base

    # Generar lista de transformaciones (fallback progresivo segun shock)
    def get_transformations(f_tech, r_tech):
        transforms = [(f_tech, r_tech)]  # Original

        if str(front_shock) == "5100":
            # Para 5100: eliminar el Rear completo
            transforms.append((f_tech, ""))
        elif str(front_shock) in ("6112", "5160") or str(rear_shock) in ("6112", "5160"):
            # Para 6112/5160: eliminar la keyword "Shocks" del Rear
            if "Shocks" in r_tech:
                transforms.append((f_tech, r_tech.replace("Shocks", "").strip()))
        elif str(front_shock) in ("8112", "8100") or str(rear_shock) in ("8112", "8100"):
            # Para DSA+ (8112 y 8100)
            # 1) Eliminar "Smooth Body" del Rear
            if "Smooth Body" in r_tech:
                transforms.append((f_tech, r_tech.replace("Smooth Body", "").strip()))
            # 2) Si no alcanza, eliminar "Zone Control CR" del Front
            if "Zone Control CR" in f_tech:
                transforms.append((f_tech.replace("Zone Control CR", "CR").strip(), r_tech))
                transforms.append((f_tech.replace("Zone Control CR", "CR").strip(), r_tech.replace("Smooth Body", "").strip() if "Smooth Body" in r_tech else r_tech))
            # 3) Si el exceso es poco, solo quitar "CR"
            if "CR" in f_tech and "Zone Control CR" not in f_tech:
                transforms.append((f_tech.replace("CR", "").strip(), r_tech))

        return transforms

    # Probar todas las transformaciones
    transforms = get_transformations(front_tech, rear_tech)
    gmc_title = None
    for f_tech, r_tech in transforms:
        candidate = build_with_tech(f_tech, r_tech)
        if len(candidate) <= GMC_TITLE_MAX_LENGTH:
            gmc_title = candidate
            break

    # Si ninguna transformacion entra, marcar con [EXCEDE]
    if gmc_title is None:
        gmc_title = title_base
        if len(gmc_title) > GMC_TITLE_MAX_LENGTH:
            gmc_title = f"{gmc_title} [EXCEDE {GMC_TITLE_MAX_LENGTH} CHARS]"

    return gmc_title
