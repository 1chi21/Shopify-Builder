"""
Funciones para generar SEO Title y GMC Title según reglas de Carlos
"""
import pandas as pd
from title_rules import (
    SHOCK_ABBREVIATIONS,
    SHOCK_TECHNOLOGY,
    GENERATION_MAP,
    SEO_TITLE_MAX_LENGTH,
    GMC_TITLE_MAX_LENGTH,
    GMC_ALTERNATIVE_TEXT,
)
from utils import clean_str, build_lift_range


def get_generation(gen_value):
    """
    Convierte el valor de Gen a formato legible para título
    Ejemplo: "5thGen" -> "5th Gen"
    """
    if pd.isna(gen_value):
        return ""
    gen_str = str(gen_value).strip()
    return GENERATION_MAP.get(gen_str, gen_str)


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


def build_seo_title(vdf_for_product, brand, shock_type, lift_range, model, year, gen, trim):
    """
    Genera SEO Title según reglas de Carlos
    Formato: MARCA_ABREVIADA SHOCK GENERACIÓN MODELO [TRIM] Lift Kit RANGO_ALTURAS (AÑOS)
    Máximo: 70 caracteres (nivel producto)
    
    Ejemplo: "OME BP-51 5th Gen 4Runner Lift Kit 2-3" (2010-2024)"
    """
    brand_abbr = get_shock_abbreviation(brand, shock_type)
    shock = clean_str(shock_type) if shock_type else ""
    generation = get_generation(gen)
    model_clean = clean_str(model) if model else ""
    trim_clean = clean_str(trim) if trim else ""
    
    # Convertir rango de alturas a formato con comillas
    # Ejemplo: "2-3 inch" -> "2-3""
    lift_formatted = lift_range.replace(" inch", '"') if lift_range else ""
    
    # Formato de años
    year_formatted = f"({year})" if year else ""
    
    # Construir título
    parts = [brand_abbr, shock, generation, model_clean]
    if trim_clean:
        parts.append(trim_clean)
    parts.extend(["Lift Kit", lift_formatted, year_formatted])
    
    # Filtrar partes vacías
    parts = [p for p in parts if p]
    
    seo_title = " ".join(parts)
    
    # Verificar límite de caracteres
    if len(seo_title) > SEO_TITLE_MAX_LENGTH:
        # Si supera el límite, marcar con advertencia
        seo_title = f"{seo_title} [EXCEDE {SEO_TITLE_MAX_LENGTH} CHARS]"
    
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
):
    """
    Genera GMC Title según reglas de Carlos
    Formato: BRAND SHOCK GENERACIÓN MODELO [ENGINE] [DRIVE] [TRIM] Lift Kit RANGO_ALTURAS (AÑOS), 
             MARCA_ABREVIADA TECNOLOGÍA_SHOCK, [SHOCK_ARCHITECTURE], [LEAF_SPRINGS], Suspension Upgrade
    Máximo: 150 caracteres (nivel variante)
    
    Ejemplo: "Old Man Emu MT64 5th Gen 4Runner Lift Kit 2-3" (2010-2024), OME Monotube Shocks, Suspension Upgrade"
    """
    brand_clean = clean_str(brand) if brand else ""
    shock = clean_str(shock_type) if shock_type else ""
    generation = get_generation(gen)
    model_clean = clean_str(model) if model else ""
    engine_clean = clean_str(engine) if engine else ""
    drive_clean = clean_str(drive) if drive else ""
    trim_clean = clean_str(trim) if trim else ""
    
    # Convertir rango de alturas a formato con comillas
    lift_formatted = lift_range.replace(" inch", '"') if lift_range else ""
    
    # Formato de años
    year_formatted = f"({year})" if year else ""
    
    # Construir primera parte del título
    parts = [brand_clean, shock, generation, model_clean]
    if engine_clean:
        parts.append(engine_clean)
    if drive_clean:
        parts.append(drive_clean)
    if trim_clean:
        parts.append(trim_clean)
    parts.extend(["Lift Kit", lift_formatted, year_formatted])
    
    # Filtrar partes vacías
    parts = [p for p in parts if p]
    title_base = " ".join(parts)
    
    # Obtener tecnología y arquitectura del shock
    brand_abbr = get_shock_abbreviation(brand, shock_type)
    technology, architecture = get_shock_technology(shock_type)
    
    # Construir segunda parte (después de la coma)
    tech_parts = []
    if brand_abbr and technology:
        tech_parts.append(f"{brand_abbr} {technology}")
    if architecture:
        tech_parts.append(architecture)
    
    # Verificar si tiene leaf springs
    if has_leaf_springs(vdf_for_variant, type_col):
        tech_parts.append("Rear Leaf Springs")
    
    # Agregar "Suspension Upgrade" al final
    tech_parts.append(GMC_ALTERNATIVE_TEXT)
    
    # Combinar todo
    if tech_parts:
        gmc_title = f"{title_base}, {', '.join(tech_parts)}"
    else:
        gmc_title = title_base
    
    # Verificar límite de caracteres
    if len(gmc_title) > GMC_TITLE_MAX_LENGTH:
        # Si supera el límite, quitar "Suspension Upgrade"
        if GMC_ALTERNATIVE_TEXT in tech_parts:
            tech_parts.remove(GMC_ALTERNATIVE_TEXT)
            if tech_parts:
                gmc_title = f"{title_base}, {', '.join(tech_parts)}"
            else:
                gmc_title = title_base
        
        # Si aún supera el límite, marcar con advertencia
        if len(gmc_title) > GMC_TITLE_MAX_LENGTH:
            gmc_title = f"{gmc_title} [EXCEDE {GMC_TITLE_MAX_LENGTH} CHARS]"
    
    return gmc_title
