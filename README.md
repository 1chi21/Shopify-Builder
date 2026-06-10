# Shopify Product Builder

Genera archivos Excel compatibles con [Matrixify](https://matrixify.app/) para importar productos a Shopify de forma masiva.

## Uso

1. Sube tu archivo `SuspensionConfigurator.xlsx`
2. Revisa el análisis automático (vendors, vehículos, columnas detectadas)
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
