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
