"""
Funciones utilitarias compartidas entre módulos
"""
import pandas as pd
import re
from datetime import datetime


def clean_str(val):
    """
    Limpia strings: convierte NaN, None, "N/A", "" a string vacío.
    Si el valor es datetime (o pd.Timestamp, subclase), extrae el año como string.
    Tambien detecta strings con formato datetime (YYYY-MM-DD...) y extrae el año.
    Esto evita que strings como "2018-07-01 00:00:00" terminen en títulos cuando
    Excel formatea celdas de año como fecha o cuando el valor llega como string.
    """
    if pd.isna(val):
        return ""
    if isinstance(val, datetime):
        return str(val.year)
    s = str(val).strip()
    if s.lower() in ("nan", "none", "n/a", ""):
        return ""
    # Detectar string con formato datetime tipo "2018-07-01 00:00:00" o "2018-07-01"
    m = re.match(r'^(\d{4})-\d{2}-\d{2}', s)
    if m:
        return m.group(1)
    return s


def build_lift_range(lift_values):
    """
    Calcula el rango total de alturas:
    - Input: ["0-2", "3-4", "5-6"]
    - Extrae todos los números: [0, 2, 3, 4, 5, 6]
    - Output: "0-6 inch"
    """
    nums = []
    for v in lift_values:
        v = clean_str(v)
        if not v:
            continue
        # Limpiar el valor de cualquier texto adicional
        v = v.replace(" inches", "").replace(" inch", "").strip()
        # Extraer TODOS los números del valor (para rangos como "0-2" extraer 0 y 2)
        matches = re.findall(r'(\d+\.?\d*)', v)
        for match in matches:
            try:
                nums.append(float(match))
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


def extract_height_str_from_sku(sku):
    """
    Extrae el string de altura (rango o valor único) del Parent Sku.
    Maneja el patron -(shock 4 digitos)-(altura)LEV$ usado en Leveling Kits.
    Retorna solo el string de altura (sin "inches"), listo para usar como valor
    normalizado en la columna de lift height.

    El regex usa un prefijo greedy con backtracking para encontrar el ULTIMO
    segmento de 4 digitos (el shock) antes de LEV, ignorando años o modelos
    que tambien puedan ser 4 digitos.

    Ejemplos:
      BILSIL-2500-0713-5100-4-6LEV      -> "4-6"
      BILSIL-2500-1418-5100-1.5LEV      -> "1.5"
      BILSIL-1500-0713-5100-0-1.75LEV   -> "0-1.75"
      BILSIL-2500-19ON-5100-4-6LEV      -> "4-6"
      SKU sin patron LEV                -> ""
    """
    m = re.search(r'^(.*)-(\d{4})-(.+?)LEV$', str(sku), re.IGNORECASE)
    if m:
        height = m.group(3).strip()
        if height:
            return height
    return ""
