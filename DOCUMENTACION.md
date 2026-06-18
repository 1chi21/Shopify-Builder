# Documentación Técnica - Shopify Product Builder

## Índice
1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Flujo de Procesamiento](#flujo-de-procesamiento)
4. [Estructura del Código](#estructura-del-código)
5. [Funciones Core](#funciones-core)
6. [Formato de Datos](#formato-de-datos)
7. [Metafields de Shopify](#metafields-de-shopify)
8. [Guía para Agregar Funcionalidades](#guía-para-agregar-funcionalidades)
9. [Solución de Problemas](#solución-de-problemas)

---

## Descripción General

Este programa convierte archivos Excel de configuración de suspensiones (SuspensionConfigurator) en archivos Excel compatibles con Matrixify para importar productos a Shopify de forma masiva.

### ¿Qué hace?
- Lee un archivo Excel con datos de kits de suspensión
- Detecta automáticamente columnas relevantes (Brand, Height, Shock, etc.)
- Genera un producto separado por cada combinación única de: **Make + Model + Year + Brand + Shock Type**
- Crea variantes basadas en: **Lift Height + Front Load + Rear Load**
- Genera un archivo Excel listo para importar en Matrixify

### ¿Por qué es importante?
- **Automatiza** la creación de cientos de productos en Shopify
- **Previene errores** de duplicación de variantes
- **Estandariza** el formato de productos
- **Ahorra tiempo** al equipo de operaciones

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    app.py (Streamlit)                    │
│              Interfaz de usuario web                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   builder.py (Core)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. parse_input() - Lee archivo Excel            │   │
│  │  2. analyze_input() - Detecta columnas           │   │
│  │  3. build_matrixify_excel() - Genera output      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Archivos Principales

| Archivo | Propósito |
|---------|-----------|
| `app.py` | Interfaz web de Streamlit, configuración de UI |
| `builder.py` | Lógica core de procesamiento y generación |
| `requirements.txt` | Dependencias de Python |
| `README.md` | Documentación básica de uso |

---

## Flujo de Procesamiento

### Paso 1: Lectura del Archivo
```python
df = parse_input(filepath)
```
- Lee el archivo Excel
- Limpia nombres de columnas (elimina espacios, caracteres invisibles)
- Retorna un DataFrame de pandas

### Paso 2: Análisis del Archivo
```python
info = analyze_input(df)
```
Detecta automáticamente:
- **Columnas de vehículo**: Make, Model, Year, Brand
- **Columnas de producto**: Height, Shock, Position, Type, Part Sku, Color
- **Columnas de variante**: Front Load, Rear Load, Pin Position, Rear Lift
- **Vendors únicos**: Lista de marcas detectadas
- **Vehículos únicos**: Combinaciones Make|Model|Year
- **Shocks únicos**: Tipos de shock detectados

### Paso 3: Generación del Excel
```python
output, summary, result_df = build_matrixify_excel(df, ...)
```

#### 3.1 Agrupación por Producto
```python
df["_veh"] = df["Make"] + "|" + df["Model"] + "|" + df["Year"] + "|" + df["Brand"] + "|" + df[shock_col]
```
Cada combinación única genera **un producto separado** en Shopify.

**Ejemplo:**
- Ford|F-350|2005-2016|Bilstein|5100 → Producto 1
- Ford|F-350|2005-2016|Bilstein|5160 → Producto 2
- Ford|F-350|2017-2022|Bilstein|5100 → Producto 3

#### 3.2 Generación de Título
```python
title = build_title(brand, shock_name, lift_range, model, year)
```

**Formato:** `MARCA SHOCK RANGO-inch Lift Kit MODELO (AÑO_ABR)`

**Ejemplos:**
- `Bilstein B8 5100 0-6-inch Lift Kit F-350 (05-16)`
- `Dobinsons IMS 2.5-inch Lift Kit GX550 (24)`

**Reglas:**
- Si vendor es "Bilstein" → marca = "Bilstein B8"
- Años se abrevian: "2005-2016" → "05-16"
- Rango de altura: mínimo-máximo de TODAS las variantes

#### 3.3 Generación de Handle
```python
handle = build_handle(title)
```
Convierte el título a URL-friendly:
- `Bilstein B8 5100 0-6-inch Lift Kit F-350 (05-16)` → `bilstein-b8-5100-0-6-inch-lift-kit-f-350-05-16`

#### 3.4 Generación de Variantes
```python
vars_df = vdf.groupby(group_cols, as_index=False).agg(agg_dict)
```

**Agrupación por variante:**
- Height (Lift Setting)
- Parent Sku (SKU único)

**Orden de variantes:**
1. Por Lift Height (numérico: 0, 2, 2.5, 3, 4, 5, 6)
2. Por Front Load (Standard → Medium → Heavy)
3. Por Rear Load (None → Standard → Medium → Heavy)

#### 3.5 Generación de In The Box
```python
in_the_box = build_in_the_box(sku_rows, qty_col, position_col, type_col, part_sku_col, is_ome)
```

**Formato:** `CANTIDAD | POSITION TYPE PART_SKU`

**Ejemplos:**
- Con Position+Type+SKU: `2 | Front Shock bil24-186018`
- Sin Position/Type: `2 | Coil Spring SKU789`
- OME (sin SKU): `2 | Front Shock`

**Reglas:**
- Si hay Position y Type → usar "Position Type"
- Si solo hay Position → usar "Position"
- Si solo hay Type → usar "Type"
- Si no hay ninguno → usar "Part Name"
- Si vendor es OME → NO incluir Part Sku

---

## Estructura del Código

### Archivos Principales

| Archivo | Propósito |
|---------|-----------|
| `app.py` | Interfaz web de Streamlit, configuración de UI |
| `builder.py` | Lógica core de procesamiento y generación |
| `title_generator.py` | Funciones para generar SEO Title y GMC Title |
| `title_rules.py` | Mapeos y reglas para generación de títulos SEO/GMC |
| `utils.py` | Funciones utilitarias compartidas (clean_str, build_lift_range) |
| `requirements.txt` | Dependencias de Python |
| `README.md` | Documentación básica de uso |
| `DOCUMENTACION.md` | Documentación técnica completa |

### builder.py - Funciones Core

#### Funciones de Detección
```python
_find_column(df, candidates)
```
Busca una columna en el DataFrame comparando contra una lista de candidatos.
- Primero busca coincidencia exacta
- Luego busca coincidencia parcial (case-insensitive, sin espacios)

**Ejemplo:**
```python
LIFT_HEIGHT_COL_CANDIDATES = ["Lift Height", "Height", "Lift", "Lift Setting"]
lift_col = _find_column(df, LIFT_HEIGHT_COL_CANDIDATES)
```

#### Funciones de Limpieza
```python
clean_str(val)
```
Limpia strings: convierte NaN, None, "N/A", "" a string vacío.

```python
normalize_lift_value(val)
```
Normaliza valores de altura:
- Preserva rangos: "0-2" → "0-2"
- Convierte números: "2.5" → "2.5"
- Extrae números de texto: "2 inch" → "2"

```python
abbreviate_year(year_str)
```
Abrevia años:
- "2005-2016" → "05-16"
- "2024" → "24"

#### Funciones de Construcción
```python
build_title(brand, shock_name, lift_range, model, year)
```
Genera el título del producto.

```python
build_handle(title)
```
Genera el handle (URL slug) del producto.

```python
build_lift_range(lift_values)
```
Calcula el rango total de alturas:
- Input: ["0-2", "3-4", "5-6"]
- Extrae todos los números: [0, 2, 3, 4, 5, 6]
- Output: "0-6 inch"

```python
build_in_the_box(vdf_for_sku, qty_col, position_col, type_col, part_sku_col, is_ome)
```
Genera el contenido de "In The Box" para cada variante.

```python
build_body_html(parts_df, qty_col)
```
Genera el HTML de la descripción del producto (tabla de componentes).

```python
build_product_metafields(vdf, lift_col, qty_col)
```
Genera metafields de producto:
- `custom.height`: Lista de alturas separadas por ";"
- `custom.load`: Lista de cargas separadas por ";"

#### Función Principal
```python
build_matrixify_excel(df, tags, status, product_type, lift_col, shock_col, ...)
```
Orquesta todo el proceso de generación del Excel.

### title_generator.py - Generación de Títulos SEO/GMC

#### Funciones de Generación
```python
build_seo_title(vdf_for_product, brand, shock_type, lift_range, model, year, gen, trim)
```
Genera SEO Title según reglas de Carlos (máximo 70 caracteres, nivel producto).

```python
build_gmc_title(vdf_for_variant, brand, shock_type, lift_range, model, year, gen, engine, drive, trim, type_col)
```
Genera GMC Title según reglas de Carlos (máximo 150 caracteres, nivel variante).

#### Funciones Auxiliares
```python
get_generation(gen_value)
```
Convierte el valor de Gen a formato legible (ej: "5thGen" → "5th Gen").

```python
get_shock_abbreviation(brand, shock_type)
```
Obtiene la abreviación de marca (ej: "Old Man Emu" → "OME").

```python
get_shock_technology(shock_type)
```
Obtiene la tecnología y arquitectura del shock.

```python
has_leaf_springs(vdf_for_product, type_col)
```
Verifica si el producto tiene leaf springs.

### title_rules.py - Reglas de Configuración

Contiene los mapeos y constantes:
- `SHOCK_ABBREVIATIONS`: Mapeo de marcas a abreviaciones
- `SHOCK_TECHNOLOGY`: Mapeo de shocks a tecnologías y arquitecturas
- `GENERATION_MAP`: Mapeo de generaciones
- `SEO_TITLE_MAX_LENGTH`: Límite de caracteres para SEO Title (70)
- `GMC_TITLE_MAX_LENGTH`: Límite de caracteres para GMC Title (150)
- `GMC_ALTERNATIVE_TEXT`: Texto alternativo cuando GMC Title supera límite

### utils.py - Funciones Utilitarias

Contiene funciones compartidas entre módulos:
```python
clean_str(val)
```
Limpia strings: convierte NaN, None, "N/A", "" a string vacío.

```python
build_lift_range(lift_values)
```
Calcula el rango total de alturas (ej: ["0-2", "3-4", "5-6"] → "0-6 inch").

---

## Formato de Datos

### Archivo de Entrada (SuspensionConfigurator.xlsx)

**Columnas Requeridas:**
| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| Make | Marca del vehículo | Ford |
| Model | Modelo del vehículo | F-350 |
| Year | Año del vehículo | 2005-2016 |
| Brand | Marca del producto | Bilstein |
| Part Name | Nombre del componente | Bilstein 5100 Series Front Shock |
| Qty / Qty Customer | Cantidad | 2 |
| Parent Sku | SKU del kit | BILF350-0516-5100-0-2LEV |
| Total Price | Precio total | 492.00 |
| Front Load | Carga frontal | Standard |
| Rear Load | Carga trasera | Stock |

**Columnas Opcionales:**
| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| Height / Lift Height | Altura del lift | 0-2 |
| Shock / Shock Type | Tipo de shock | 5100 |
| Position | Posición de la parte | Front |
| Type | Tipo de parte | Shock |
| Part Sku | SKU del componente | bil24-186018 |
| Pin Position for Install | Posición del pin | 1 |
| Rear Lift | Rear lift height | 0-1 |
| Color | Color del producto | Black |
| Gen | Generación del vehículo | 5thGen |
| Engine | Tipo de motor | Gas |
| Drive | Tipo de tracción | 4WD |
| Trim | Trim del vehículo | w/ KDSS |

### Archivo de Salida (matrixify_products.xlsx)

**Columnas Principales:**
| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| Handle | URL slug | bilstein-b8-5100-0-6-inch-lift-kit-f-350-05-16 |
| Command | Acción de Matrixify | NEW |
| Title | Título del producto | Bilstein B8 5100 0-6-inch Lift Kit F-350 (05-16) |
| Body HTML | Descripción HTML | `<table>...</table>` |
| Vendor | Marca | Bilstein |
| Type | Tipo de producto | Lift Kits |
| Tags | Etiquetas | Full Lift Kit, Liftkit |
| Status | Estado | Draft |
| Option1 Name | Nombre opción 1 | Select Desired Lift Setting |
| Option1 Value | Valor opción 1 | 0-2 inches |
| Option2 Name | Nombre opción 2 | Select Front Load (Constant) |
| Option2 Value | Valor opción 2 | Standard (Up to 50 lbs) |
| Option3 Name | Nombre opción 3 | Select Rear Load (Constant) |
| Option3 Value | Valor opción 3 | Standard (Up to 200 lbs) |
| Variant SKU | SKU de variante | BILF350-0516-5100-0-2LEV |
| Variant Price | Precio de variante | 492.00 |

---

## Metafields de Shopify

### Metafields de Producto

#### custom.height
- **Tipo:** list.single_line_text_field
- **Formato:** Valores separados por ";"
- **Ejemplo:** `0-2 inch;3-4 inch;5-6 inch`
- **Propósito:** Lista de alturas disponibles del kit

#### custom.load
- **Tipo:** list.single_line_text_field
- **Formato:** Valores separados por ";"
- **Ejemplo:** `Standard;Medium;Heavy`
- **Propósito:** Lista de cargas frontales disponibles

#### custom.color
- **Tipo:** list.single_line_text_field
- **Formato:** Valores separados por ";"
- **Ejemplo:** `Black;Red;Blue`
- **Propósito:** Colores disponibles (solo para Dobinsons)
- **Regla:** Solo se genera si vendor contiene "dobinsons"

#### title_tag (SEO Title)
- **Tipo:** string
- **Formato:** `MARCA_ABREVIADA SHOCK GENERACIÓN MODELO [TRIM] Lift Kit RANGO_ALTURAS (AÑOS)`
- **Ejemplo:** `OME BP-51 5th Gen 4Runner Lift Kit 2-3" (2010-2024)`
- **Propósito:** Título SEO para Google (máximo 70 caracteres)
- **Regla:** Solo se genera para productos Old Man Emu
- **Columnas requeridas:** Gen, Trim (opcionales)

### Metafields de Variante

#### custom.in_the_box
- **Tipo:** multi_line_text_field
- **Formato:** `CANTIDAD | POSITION TYPE PART_SKU`
- **Ejemplo:** `2 | Front Shock bil24-186018 | 2 | Rear Shock bil24-186025`
- **Propósito:** Contenido del kit

#### custom.lift_range
- **Tipo:** single_line_text_field
- **Formato:** `HEIGHT|REAR_LIFT`
- **Ejemplo:** `0-2|0-1`
- **Propósito:** Rango de altura frontal y trasera

#### custom.shock_position
- **Tipo:** single_line_text_field
- **Ejemplo:** `1`
- **Propósito:** Posición del pin para instalación

#### custom.shipping_ome_bilstein
- **Tipo:** single_line_text_field
- **Valor:** `Shipping OME / Bilstein`
- **Regla:** Solo se llena si vendor contiene "old man emu", "ome" o "bilstein"

#### custom.shipping_dobinsons
- **Tipo:** single_line_text_field
- **Valor:** `Shipping Dobinsons`
- **Regla:** Solo se llena si vendor contiene "dobinsons"

#### custom.gmc_title (GMC Title)
- **Tipo:** single_line_text_field
- **Formato:** `BRAND SHOCK GENERACIÓN MODELO [ENGINE] [DRIVE] [TRIM] Lift Kit RANGO_ALTURAS (AÑOS), MARCA_ABREVIADA TECNOLOGÍA_SHOCK, [SHOCK_ARCHITECTURE], [LEAF_SPRINGS], Suspension Upgrade`
- **Ejemplo:** `Old Man Emu MT64 5th Gen 4Runner Lift Kit 2-3" (2010-2024), OME Monotube Shocks, Suspension Upgrade`
- **Propósito:** Título para Google Merchant Center (máximo 150 caracteres)
- **Regla:** Solo se genera para productos Old Man Emu
- **Columnas requeridas:** Gen, Engine, Drive, Trim (opcionales)
- **Límite:** Si supera 150 caracteres, se quita "Suspension Upgrade". Si aún supera, se marca con advertencia.

---

## Reglas de Generación de Títulos SEO/GMC

### Archivos de Configuración

- **title_rules.py:** Contiene los mapeos de shocks a tecnologías y arquitecturas
- **title_generator.py:** Contiene las funciones `build_seo_title` y `build_gmc_title`

### Mapeo de Shocks a Tecnologías

| Shock | Tecnología | Arquitectura |
|-------|-----------|--------------|
| BP-51 | Bypass Shocks | Remote Reservoir, Adjustable Coilover |
| MT64 | Monotube Shocks | - |
| Nitrocharger | Twin Tube Shocks | - |
| Nitro | Twin Tube Shocks | - |

### Mapeo de Generaciones

| Gen (Input) | Formato (Output) |
|-------------|------------------|
| 5thGen | 5th Gen |
| 4thGen | 4th Gen |
| 3rdGen | 3rd Gen |
| 2ndGen | 2nd Gen |
| 1stGen | 1st Gen |
| 2nd & 3rd Gen | 2nd & 3rd Gen |

### Reglas de SEO Title (Nivel Producto)

**Formato:** `MARCA_ABREVIADA SHOCK GENERACIÓN MODELO [TRIM] Lift Kit RANGO_ALTURAS (AÑOS)`

**Ejemplos:**
- `OME BP-51 5th Gen 4Runner Lift Kit 2-3.5" (2010-2024)` - 53 chars
- `OME MT64 5th Gen 4Runner Lift Kit 2-3" (2010-2024)` - 50 chars
- `OME Nitrocharger 5th Gen 4Runner w/ KDSS Lift Kit 2-3" (2010-2024)` - 66 chars

**Límite:** 70 caracteres máximo

### Reglas de GMC Title (Nivel Variante)

**Formato:** `BRAND SHOCK GENERACIÓN MODELO [ENGINE] [DRIVE] [TRIM] Lift Kit RANGO_ALTURAS (AÑOS), MARCA_ABREVIADA TECNOLOGÍA_SHOCK, [SHOCK_ARCHITECTURE], [LEAF_SPRINGS], Suspension Upgrade`

**Ejemplos:**
- `Old Man Emu MT64 5th Gen 4Runner Lift Kit 2-3" (2010-2024), OME Monotube Shocks, Suspension Upgrade` - 99 chars
- `Old Man Emu BP-51 5th Gen 4Runner w/ KDSS Lift Kit 2-3" (2010-2024), OME Bypass Shocks, Remote Reservoir, Adjustable Coilovers, Suspension Upgrade` - 146 chars

**Límite:** 150 caracteres máximo
- Si supera 150 caracteres → quitar "Suspension Upgrade"
- Si aún supera → marcar con advertencia `[EXCEDE 150 CHARS]`

### Detección de Leaf Springs

La función `has_leaf_springs()` busca en la columna `Type` valores que contengan:
- "leaf"
- "leaf spring"
- "rear leaf"

Si encuentra alguno, agrega "Rear Leaf Springs" al GMC Title.

---

## Guía para Agregar Funcionalidades

### Principios Fundamentales

1. **NO modificar funciones existentes** a menos que sea absolutamente necesario
2. **Agregar código nuevo** en lugar de sobrescribir
3. **Mantener backward compatibility** - lo que funciona hoy debe seguir funcionando mañana
4. **Pensar en extensiones**, no en reemplazos
5. **Documentar claramente** qué es core y qué son features agregadas

### Ejemplo: Agregar un Nuevo Metafield

**Situación:** Quieres agregar un metafield `custom.installation_time` que muestre el tiempo de instalación.

**Paso 1:** Agregar la columna a COLS en builder.py
```python
COLS = [
    # ... columnas existentes ...
    "Variant Metafield: custom.installation_time [single_line_text_field]",
]
```

**Paso 2:** Agregar detección de columna (si aplica)
```python
INSTALLATION_TIME_COL_CANDIDATES = [
    "Installation Time", "Install Time", "install_time",
]
```

**Paso 3:** Agregar detección en analyze_input()
```python
info["installation_time_col"] = _find_column(df, INSTALLATION_TIME_COL_CANDIDATES)
```

**Paso 4:** Agregar parámetro a build_matrixify_excel()
```python
def build_matrixify_excel(df, ..., installation_time_col=None):
    if installation_time_col is None:
        installation_time_col = _find_column(df, INSTALLATION_TIME_COL_CANDIDATES)
```

**Paso 5:** Generar el valor en el loop de variantes
```python
install_time = clean_str(row.get(installation_time_col, "")) if installation_time_col else ""
```

**Paso 6:** Asignar al variant row
```python
vr.update({
    # ... otros campos ...
    "Variant Metafield: custom.installation_time [single_line_text_field]": install_time,
})
```

**Paso 7:** Actualizar app.py para pasar el parámetro
```python
output, summary, result_df = build_matrixify_excel(
    df,
    # ... otros parámetros ...
    installation_time_col=info['installation_time_col'],
)
```

**Paso 8:** Actualizar UI en app.py para mostrar la columna detectada
```python
if info.get('installation_time_col'):
    st.success(f"Columna Installation Time: {info['installation_time_col']}")
```

### Ejemplo: Agregar una Nueva Función de Procesamiento

**Situación:** Quieres agregar una función que calcule el peso total del kit.

**Paso 1:** Crear la función en builder.py
```python
def calculate_total_weight(vdf_for_sku, weight_col):
    """
    Calcula el peso total sumando el peso de cada componente.
    Retorna el peso total en libras.
    """
    if not weight_col or weight_col not in vdf_for_sku.columns:
        return ""
    
    total = 0
    for _, r in vdf_for_sku.iterrows():
        weight = clean_str(r.get(weight_col, ""))
        qty = int(r["Qty"]) if pd.notna(r["Qty"]) else 1
        try:
            total += float(weight) * qty
        except:
            pass
    
    return str(total) if total > 0 else ""
```

**Paso 2:** Llamar la función donde sea necesario
```python
total_weight = calculate_total_weight(sku_rows, weight_col)
```

**Paso 3:** Asignar al campo correspondiente
```python
vr.update({
    "Variant Weight": total_weight,
})
```

### Ejemplo: Modificar una Función Existente (Último Recurso)

**Situación:** Necesitas modificar `build_title` para agregar un prefijo personalizado.

**ANTES de modificar:**
1. Documenta por qué es necesario modificar la función
2. Identifica todos los lugares donde se llama la función
3. Asegúrate de que el cambio sea backward compatible

**Modificación segura:**
```python
def build_title(brand, shock_name, lift_range, model, year, prefix=""):
    """
    Genera el título del producto.
    
    Args:
        prefix: Prefijo opcional (nuevo parámetro con valor por defecto)
    """
    if "bilstein" in brand.lower():
        marca = "Bilstein B8"
    else:
        marca = brand
    
    shock = shock_name if shock_name else ""
    lift_clean = lift_range.replace(" inch", "-inch") if lift_range else ""
    model_clean = model
    year_abbr = abbreviate_year(year) if year else ""
    
    parts = [p for p in [prefix, marca, shock, lift_clean, "Lift Kit", model_clean, f"({year_abbr})"] if p]
    return " ".join(parts)
```

**Clave:** El nuevo parámetro `prefix` tiene un valor por defecto `""`, por lo que todas las llamadas existentes seguirán funcionando sin cambios.

---

## Solución de Problemas

### Problema: Las variantes muestran valores incorrectos

**Síntoma:** Option1 Value muestra "0 inches" en lugar de "0-2 inches"

**Causa:** La función `normalize_lift_value` estaba extrayendo solo el primer número.

**Solución:** Se modificó para preservar rangos:
```python
if "-" in s:
    s = s.replace(" inches", "").replace(" inch", "").strip()
    return s  # Preserva el rango
```

### Problema: El título no muestra el rango total

**Síntoma:** Título muestra "0-2 inch" en lugar de "0-6 inch"

**Causa:** La función `build_lift_range` solo extraía el primer número de cada variante.

**Solución:** Se modificó para extraer TODOS los números:
```python
matches = re.findall(r'(\d+\.?\d*)', v)  # Extrae todos los números
for match in matches:
    nums.append(float(match))
```

### Problema: Las columnas no se detectan

**Síntoma:** La app dice "Columna Position no encontrada" pero la columna existe

**Causa:** Los nombres de columnas tienen caracteres invisibles o espacios.

**Solución:** Se mejoró la limpieza en `parse_input`:
```python
df.columns = [str(c).strip().replace('\xa0', ' ').replace('\u200b', '').replace('\t', ' ') for c in df.columns]
df.columns = [re.sub(r'\s+', ' ', c).strip() for c in df.columns]
```

### Problema: In The Box muestra nombres muy largos

**Síntoma:** `2 | Bilstein 5100 Series Ford F-250/F-350 Super Duty 4WD Front 46mm Monotube Shock Absorber`

**Causa:** Se estaba usando Part Name completo.

**Solución:** Se modificó para usar Position + Type cuando estén disponibles:
```python
if position and part_type:
    desc = f"{position} {part_type}"  # "Front Shock"
elif position:
    desc = position
elif part_type:
    desc = part_type
else:
    desc = nm  # Part Name como fallback
```

---

## Versiones y Changelog

### v1.8.10 (2026-06-18) - Versión Actual
- **Bug fix orden de variantes**: `sort_variants` ahora extrae el primer número del rango de altura (ej: "4-6" → 4, "2-2.5" → 2) en lugar de hacer `float()` directo que fallaba con rangos. Corrige el orden ascendente para productos con alturas-rango.
- **Bug fix altura vacía (nan)**: Fallback en `build_matrixify_excel` que extrae la altura del Parent Sku cuando la columna Height tiene valores inválidos (datetime, NaN). Nueva función `extract_height_str_from_sku()` en `utils.py` con regex `^(.*)-(\d{4})-(.+?)LEV$`.
- **Aislamiento**: Solo afecta Tab 1. Tab 2 (SEO & GMC Titles) intacta.

### v1.8.9 (2026-06-17)
- **Columna ID agregada al output**: El archivo de Excel ahora incluye el ID del producto en Shopify para fácil identificación en Matrixify

### v1.8.8 (2026-06-17)
- **Bug fix**: Corregido error NameError cuando no hay columna ID (usaba variable `vk` no definida)

### v1.8.7 (2026-06-17)
- **SEO Title por ID de producto**: El SEO Title ahora se agrupa por la columna "ID" del archivo (1 por producto en Shopify)
- **GMC Title por variante**: El GMC Title sigue siendo por variante como antes
- **Fallback automático**: Si no hay columna "ID", se usa el agrupamiento por vehículo (comportamiento anterior)

### v1.8.6 (2026-06-17)
- **ASS como diferenciador de producto**: Variantes con "-ASS" en su SKU (assembled) ahora se separan en productos diferentes
- **Handle incluye ASS**: El handle ahora también incluye "-ass" al final cuando el SKU tiene "-ASS" (ej: `-ass`)

### v1.8.5 (2026-06-17)
- **Leveling Kit por variante**: Cada variante ahora detecta su tipo (Leveling/Lift) desde la columna "Internal Type" de su SKU
- **GMC Title correcto por variante**: Variantes con "Leveling" en Internal Type ahora muestran "Leveling Kit" en el título

### v1.8.4 (2026-06-17)
- **Leveling Kit detection**: Si el producto es "Leveling Kit" (en Internal Type o Type), el título ahora dice "Leveling Kit" en lugar de "Lift Kit"
- **Aplica a SEO Title y GMC Title**: Ambas pestañas generan el tipo de kit correcto

### v1.8.3 (2026-06-17)
- **Drive como diferenciador de producto**: Variantes con diferente Drive (4WD, 2WD, Both, etc.) ahora se separan en productos diferentes
- **Handle incluye Drive**: El handle ahora también incluye el Drive al final (ej: `-4wd`, `-2wd`)

### v1.8.2 (2026-06-17)
- **Trim como diferenciador de producto**: Variantes con diferente Trim (V8, KDSS, RWD, etc.) ahora se separan en productos diferentes
- **Handle incluye Trim**: El handle ahora incluye el Trim al final para evitar duplicados (ej: `-v8`, `-kdss`)

### v1.8.1 (2026-06-17)
- **Shock Nitro → Nitrocharger**: Si el shock dice "Nitro", ahora se muestra como "Nitrocharger" en los títulos SEO/GMC
- **Engine "Gas" omitido**: Si el engine dice "Gas", ya no se incluye en el GMC Title (se sobreentiende). Otros valores (Diesel, Hybrid, etc.) sí se incluyen

### v1.8.0 (2026-06-17)
- **Nueva pestaña "SEO & GMC Titles"**: Para actualizar títulos de productos existentes sin crear nuevos
- **Archivo de actualización**: Genera Excel con solo Handle, Command UPDATE, y metafields SEO/GMC
- **Verificación de límites**: Advierte cuando SEO Titles superan 70 caracteres

### v1.7.0 (2026-06-17)
- **SEO Title**: Nuevo metafield `title_tag` generado según reglas de Carlos (máximo 70 caracteres, nivel producto)
- **GMC Title**: Nuevo metafield `custom.gmc_title` generado según reglas de Carlos (máximo 150 caracteres, nivel variante)
- **Nuevos archivos**: `title_generator.py`, `title_rules.py`, `utils.py` para generación de títulos SEO/GMC
- **Detección de columnas**: Gen, Engine, Drive, Trim para generación de títulos SEO/GMC
- **Solo para Old Man Emu**: Por ahora solo aplica a productos OME
- **Refactorización**: Movidas funciones `clean_str` y `build_lift_range` a `utils.py` para evitar importación circular

### v1.6.8 (2026-06-10)
- **Título corregido**: "inch" ahora aparece separado por espacio en lugar de guión

### v1.6.7 (2026-06-10)
- **Variantes corregidas**: Option1 Value ahora muestra rangos completos como "0-2 inches", "3-4 inches", "5-6 inches"
- **Título con rango total**: Muestra el rango mínimo-máximo de todas las variantes (ej: "0-6 inch")

### v1.6.6 (2026-06-10)
- **Rango total en título**: Ahora calcula el rango mínimo-máximo de TODAS las variantes

### v1.6.5 (2026-06-10)
- **Rangos de altura corregidos**: Ahora preserva rangos como "0-2", "3-4", "5-6"

### v1.6.4 (2026-06-10)
- **In the box corregido**: Ahora usa correctamente Position + Type

### v1.6.3 (2026-06-10)
- **In the box simplificado**: Ahora usa solo Position + Type

### v1.6.2 (2026-06-10)
- **Rango de alturas en título**: Corregido para que siempre se incluya
- **Normalización de lift height**: Ahora extrae números de texto

### v1.6.1 (2026-06-10)
- **Detección de columnas mejorada**: Ahora detecta variaciones como "PartSku", "Pos", "PartType"

### v1.6.0 (2026-06-10)
- **Título corregido**: Formato `MARCA SHOCK ALTURA-inch Lift Kit MODELO (AÑO)`
- **In the box mejorado**: Usa Position + Type + Part Name

### v1.5.0 (2026-06-10)
- **In the box formato corto**: Usa columna "Part Sku" para el numero de parte
- **OME sin SKU**: Cuando vendor es Old Man Emu/OME, no incluye numero de parte

### v1.4.0 (2026-06-10)
- **Sell without stock**: `Inventory Policy` → `continue`
- **Producto físico**: `Requires Shipping` → `TRUE`
- **Handle nuevo formato**: `MARCA_SHOCK_ALTURA-INCH_LIFT-KIT_MODELO_AÑO`
- **Bilstein B8**: Marca "Bilstein-B8" si vendor es Bilstein
- **Metafield de color**: `custom.color` para vendor Dobinsons

### v1.3.0 (2026-06-10)
- **Metafields de producto**: `custom.height` y `custom.load`
- **Metafields de variante**: `custom.in_the_box`, `custom.lift_range`, `custom.shock_position`, `custom.shipping_ome_bilstein`, `custom.shipping_dobinsons`

### v1.2.0 (2026-06-10)
- **Años abreviados en título**: "2024-2026" → "(24-26)"

### v1.1.0 (2026-06-10)
- **Shock como diferenciador de producto**: Cada tipo de shock genera un producto separado
- **Título mejorado**: Incluye nombre del shock y rango de alturas
- **Orden de variantes**: Standard → Medium → Heavy

### v1.0.0 (2026-06-10)
- Versión inicial
- Generación de Excel compatible con Matrixify
- 3 opciones de variante: Lift Setting + Front Load + Rear Load

---

## Contacto y Soporte

Para preguntas o problemas con el programa:
1. Revisa esta documentación
2. Verifica que estés usando la última versión
3. Revisa los logs de Streamlit Cloud para errores específicos
4. Contacta al equipo de desarrollo

---

**Última actualización:** 2026-06-18  
**Versión actual:** 1.8.10  
**Mantenido por:** Equipo de Desarrollo
