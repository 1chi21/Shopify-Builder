"""
Configuración de reglas para generación de SEO Title y GMC Title
"""

# Mapeo de shocks a marca abreviada
SHOCK_ABBREVIATIONS = {
    "Old Man Emu": "OME",
}

# Mapeo de shocks a tecnología y arquitectura
SHOCK_TECHNOLOGY = {
    "BP-51": {
        "technology": "Bypass Shocks",
        "architecture": "Remote Reservoir, Adjustable Coilover",
    },
    "MT64": {
        "technology": "Monotube Shocks",
        "architecture": "",
    },
    "Nitrocharger": {
        "technology": "Twin Tube Shocks",
        "architecture": "",
    },
    "Nitro": {
        "technology": "Twin Tube Shocks",
        "architecture": "",
    },
}

# Mapeo de generaciones (Gen -> formato para título)
GENERATION_MAP = {
    "5thGen": "5th Gen",
    "4thGen": "4th Gen",
    "3rdGen": "3rd Gen",
    "2ndGen": "2nd Gen",
    "1stGen": "1st Gen",
    "2nd & 3rd Gen": "2nd & 3rd Gen",
}

# Límites de caracteres
# SEO_TITLE_MAX_LENGTH = 70  # Removido en v1.9.4: ya no hay límite en SEO Title
GMC_TITLE_MAX_LENGTH = 150

# Texto alternativo para GMC Title cuando supera límite
GMC_ALTERNATIVE_TEXT = "Suspension Upgrade"

# Texto que se inserta en SEO/GMC Title para productos con Assembly (-ASS en SKU)
ASSEMBLY_TEXT = "w/ Strut Assembly"

# Mapeo de shocks Bilstein a tecnologia Front/Rear
# Segun archivo de referencia SEO_GMC Titles - BILSTEIN.xlsx
# Confirmado por Carlos: el 6112 NO es coilover, es "Adjustable Shocks" (igual que 5100)
# Usado para construir el GMC Title de productos Bilstein
BILSTEIN_SHOCK_TECH = {
    "5100": {"front": "Adjustable Shocks", "rear": "Monotube Shocks"},
    "5160": {"front": "", "rear": "Remote Reservoir Shocks"},
    "6112": {"front": "Adjustable Shocks", "rear": ""},
    "8100": {"front": "", "rear": "Bypass Shocks / DSA Shocks"},
    "8112": {"front": "Zone Control Shocks / DSA Shocks", "rear": ""},
}
