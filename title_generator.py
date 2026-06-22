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
    # Si es un año o rango de años (ej: "2018", "2010-2016", "2010-16", "14-18"), ignorar
    # \d{2,4} acepta tanto 2 digitos (14-18) como 4 digitos (2010-2016)
    if re.match(r'^\d{2,4}(-\d{2,4})?$', gen_str):
        print(f"[DEBUG get_generation] Gen filtrado (year/range): {gen_str!r}")
        return ""
    return GENERATION_MAP.get(gen_str, gen_str)


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
    Determina si el producto es un "Leveling Kit" o "Lift Kit"
    basándose en el valor de Internal Type o buscando en el DataFrame.
    Retorna "Leveling Kit" si detecta "Leveling", "Lift Kit" en caso contrario.
    """
    # Si se pasa el valor directo de Internal Type, usarlo
    if internal_type_value is not None and not pd.isna(internal_type_value):
        if "leveling" in str(internal_type_value).lower():
            return "Leveling Kit"
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
    model_clean = clean_str(model) if model else ""
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
    if trim_clean:
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
    model_clean = clean_str(model) if model else ""
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
    if trim_clean:
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
