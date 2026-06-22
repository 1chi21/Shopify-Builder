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
SEO_TITLE_MAX_LENGTH = 70
GMC_TITLE_MAX_LENGTH = 150

# Texto alternativo para GMC Title cuando supera límite
GMC_ALTERNATIVE_TEXT = "Suspension Upgrade"

# Texto que se inserta en SEO/GMC Title para productos con Assembly (-ASS en SKU)
ASSEMBLY_TEXT = "w/ Strut Assembly"
