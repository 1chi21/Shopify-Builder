# Shopify Product Builder

Genera archivos Excel compatibles con [Matrixify](https://matrixify.app/) para importar productos a Shopify de forma masiva.

## Uso

1. Sube tu archivo `SuspensionConfigurator.xlsx`
2. Revisa el análisis automático (vendors, vehículos, shocks detectados)
3. Ajusta Tags, Status y Product Type si es necesario
4. Haz clic en "Generar Excel"
5. Descarga el archivo `matrixify_products.xlsx`
6. Súbelo a Matrixify en Shopify

## Formato del archivo de entrada

Columnas requeridas en `SuspensionConfigurator.xlsx`:

| Columna | Descripción |
|---------|-------------|
| Make | Marca del vehículo |
| Model | Modelo del vehículo |
| Year | Año |
| Brand | Marca del producto (se usa como Vendor) |
| Part Name | Nombre del componente |
| Qty / Qty Customer | Cantidad |
| Parent Sku | SKU del producto |
| Total Price | Precio |
| Front Load | Carga frontal (Standard, Medium, Heavy, etc.) |
| Rear Load | Carga trasera (Standard, Medium, Heavy, etc.) |
| Height / Lift Height | Altura del lift (opcional, se puede extraer del SKU) |
| Shock / Shock Type | Tipo de shock (opcional, cada shock genera un producto separado) |
| Pin Position for Install | Posición del pin para instalación (metafield shock_position) |
| Rear Lift | Rear lift height (metafield lift_range) |
| Color | Color del producto (metafield custom.color, solo para Dobinsons) |
| Part Sku | Numero de parte del componente (para in_the_box) |
| Position | Posición de la parte (Front, Rear, etc.) |
| Type | Tipo de parte (Coil Spring, Shock, Top Hat, etc.) |

## Metafields incluidos

### Metafields de producto
- `custom.height` - Lista de alturas separada por `;` (ej: `2 inch;2.5 inch;3 inch`)
- `custom.load` - Lista de cargas frontales separada por `;` (ej: `Standard;Medium;Heavy`)
- `custom.color` - Lista de colores separada por `;` (solo para vendor Dobinsons)

### Metafields de variante
- `custom.in_the_box` - Contenido de la variante (Part Names + Qty)
- `custom.lift_range` - Rango de lift en formato "Height|Rear Lift"
- `custom.shock_position` - Posición del pin (de columna "Pin Position for Install")
- `custom.shipping_ome_bilstein` - "Shipping OME / Bilstein" si vendor es OME/Bilstein
- `custom.shipping_dobinsons` - "Shipping Dobinsons" si vendor es Dobinsons

## Características

- **Sell without stock**: Siempre activo (`Inventory Policy: continue`)
- **Producto físico**: `Requires Shipping: TRUE`
- **Handle formato**: `MARCA_SHOCK_ALTURA-INCH_LIFT-KIT_MODELO_AÑO` (ej: `dobinsons_ims_2.5-inch_lift-kit_gx550_24`)
- **Bilstein B8**: Si vendor es Bilstein, la marca en el handle es "Bilstein-B8"
- **Shock como diferenciador de producto**: Cada tipo de shock genera un producto separado
- **Título inteligente**: Incluye nombre del shock y rango de alturas
- **Orden de variantes**: Standard → Medium → Heavy
- **3 opciones de variante**: Lift Setting + Front Load + Rear Load
- **Detección automática**: Vendors, vehículos, columnas de lift, shock, color, pin position, rear lift
- **Un solo archivo Excel**: Con sheet "Products" listo para Matrixify

## Instalación local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy en Streamlit Cloud

1. Sube este repo a GitHub
2. Ve a [streamlit.io](https://streamlit.io) y crea una nueva app
3. Conecta con tu repo de GitHub
4. Main file: `app.py`
5. Deploy automático en cada push

## Changelog

### v1.8.11 (2026-06-18)
- **Selector de pesos por variante**: Nueva sección en Tab 1 después del análisis del archivo. Permite asignar peso (en lbs) por cada nivel de Front Load y Rear Load detectado. El peso total de la variante = Front + Rear.
- **Inputs contextuales**: Solo se muestran campos para los valores de carga que aparecen en el archivo (mapeados a su valor final, ej: "Standard (Up to 50 lbs)").
- **Backward compatible**: Si no se llenan pesos, `Variant Weight` queda vacío (comportamiento previo).
- **Sin session state**: Inputs vacíos en cada nuevo análisis.

### v1.8.10 (2026-06-18)
- **Bug fix orden de variantes**: `sort_variants` ahora extrae el primer número del rango de altura (ej: "4-6" → 4, "2-2.5" → 2) en lugar de hacer `float()` directo que fallaba con rangos. Esto corrige el orden ascendente de variantes para productos con alturas-rango.
- **Bug fix altura vacía (nan)**: Cuando la columna Height tiene valores inválidos (datetime, NaN) en el input, la app ahora extrae la altura del Parent Sku como fallback (patrón `-{shock}-{altura}LEV$`). Esto corrige el problema donde variantes con altura-rango aparecían sin nombre (Option1="nan") en el output.
- **Aislamiento**: Ambos fixes solo afectan Tab 1 (Crear Productos). Tab 2 (SEO & GMC Titles) queda intacta.

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
- **Detección de columnas**: Gen, Engine, Drive, Trim para generación de títulos SEO/GMC
- **Solo para Old Man Emu**: Por ahora solo aplica a productos OME

### v1.6.8 (2026-06-10)
- **Título corregido**: "inch" ahora aparece separado por espacio en lugar de guión (ej: "0-6 inch" en lugar de "0-6-inch")

### v1.6.7 (2026-06-10)
- **Variantes corregidas**: Option1 Value ahora muestra rangos completos como "0-2 inches", "3-4 inches", "5-6 inches"
- **Título con rango total**: Muestra el rango mínimo-máximo de todas las variantes (ej: "0-6 inch")

### v1.6.6 (2026-06-10)
- **Rango total en título**: Ahora calcula el rango mínimo-máximo de TODAS las variantes (ej: variantes "0-2", "3-4", "5-6" → título muestra "0-6 inch")

### v1.6.5 (2026-06-10)
- **Rangos de altura corregidos**: Ahora preserva rangos como "0-2", "3-4", "5-6" en lugar de extraer solo el primer número
- **Variantes correctas**: Option1 Value ahora muestra "0-2 inches", "3-4 inches", etc.

### v1.6.4 (2026-06-10)
- **In the box corregido**: Ahora usa correctamente Position + Type (ej: "Front Shock SKU123")
- **Formato final**: `2 | Front Shock SKU123 | 2 | Rear Shock SKU456`

### v1.6.3 (2026-06-10)
- **In the box simplificado**: Ahora usa solo Position + Type (ej: "Front Shock")
- **Formato más corto**: `2 | Front Shock SKU123 | 2 | Rear Shock SKU456`

### v1.6.2 (2026-06-10)
- **Rango de alturas en título**: Corregido para que siempre se incluya
- **Normalización de lift height**: Ahora extrae números de texto como "2 inch" → "2"

### v1.6.1 (2026-06-10)
- **Detección de columnas mejorada**: Ahora detecta variaciones como "PartSku", "Pos", "PartType"
- **Limpieza de nombres de columnas**: Elimina caracteres invisibles y normaliza espacios

### v1.6.0 (2026-06-10)
- **Título corregido**: Formato `MARCA SHOCK ALTURA-inch Lift Kit MODELO (AÑO)`
- **Handle**: Se genera automáticamente del título
- **In the box mejorado**: Usa Position + Type + Part Name
- **Detección de columnas**: Position, Type, Part Sku

### v1.5.0 (2026-06-10)
- **In the box formato corto**: `2x Coil Spring (SKU123) | 2x Rear Shock (SKU456)`
- **Part Sku**: Usa columna "Part Sku" para el numero de parte
- **OME sin SKU**: Cuando vendor es Old Man Emu/OME, no incluye numero de parte

### v1.4.0 (2026-06-10)
- **Sell without stock**: `Inventory Policy` → `continue`
- **Producto físico**: `Requires Shipping` → `TRUE`
- **Handle nuevo formato**: `MARCA_SHOCK_ALTURA-INCH_LIFT-KIT_MODELO_AÑO`
- **Bilstein B8**: Marca "Bilstein-B8" si vendor es Bilstein
- **Metafield de color**: `custom.color` para vendor Dobinsons (columna "Color")
- **Metafields de producto**: Formato `;` separado en vez de JSON

### v1.3.0 (2026-06-10)
- **Metafields de producto**: `custom.height` y `custom.load`
- **Metafields de variante**: `custom.in_the_box`, `custom.lift_range`, `custom.shock_position`, `custom.shipping_ome_bilstein`, `custom.shipping_dobinsons`
- **Detección automática** de columnas "Pin Position for Install" y "Rear Lift"
- **Shipping automático** según vendor

### v1.2.0 (2026-06-10)
- **Años abreviados en título**: "2024-2026" → "(24-26)"

### v1.1.0 (2026-06-10)
- **Shock como diferenciador de producto**: Cada tipo de shock ahora genera un producto separado
- **Título mejorado**: Incluye nombre del shock y rango de alturas
- **Orden de variantes**: Standard → Medium → Heavy
- **Detección automática de columna Shock**

### v1.0.0 (2026-06-10)
- Versión inicial
- Generación de Excel compatible con Matrixify
- 3 opciones de variante: Lift Setting + Front Load + Rear Load
