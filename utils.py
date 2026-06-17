"""
Funciones utilitarias compartidas entre módulos
"""
import pandas as pd
import re
from datetime import datetime


def clean_str(val):
    """
    Limpia strings: convierte NaN, None, "N/A", "" a string vacío
    """
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", "n/a", ""):
        return ""
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
