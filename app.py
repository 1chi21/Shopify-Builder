import streamlit as st
import pandas as pd
from builder import parse_input, analyze_input, build_matrixify_excel

APP_VERSION = "1.6.4"

CHANGELOG = """
### v1.6.4 (2026-06-10)
- **In the box corregido**: Ahora usa correctamente Position + Type (ej: "Front Shock SKU123")
- **Formato final**: `2 | Front Shock SKU123 | 2 | Rear Shock SKU456`

### v1.6.3 (2026-06-10)
- **In the box simplificado**: Ahora usa solo Position + Type (ej: "Front Shock") en lugar de Part Name completo
- **Formato más corto**: `2 | Front Shock SKU123 | 2 | Rear Shock SKU456`

### v1.6.2 (2026-06-10)
- **Rango de alturas en título**: Corregido para que siempre se incluya (ej: "Bilstein B8 5100 2-3-inch Lift Kit F-250 (17-22)")
- **Normalización de lift height**: Ahora extrae números de texto como "2 inch" → "2"

### v1.6.1 (2026-06-10)
- **Detección de columnas mejorada**: Ahora detecta variaciones como "PartSku", "Pos", "PartType"
- **Limpieza de nombres de columnas**: Elimina caracteres invisibles y normaliza espacios

### v1.6.0 (2026-06-10)
- **Título corregido**: Formato `MARCA SHOCK ALTURA-inch Lift Kit MODELO (AÑO)` (ej: `Dobinsons IMS 2.5-inch Lift Kit GX550 (24)`)
- **Handle**: Se genera automáticamente del título
- **In the box mejorado**: Usa columnas Position + Type + Part Name (ej: `2 | Front Coil Spring | Part Name (SKU)`)
- **Detección de columnas**: Position, Type, Part Sku

### v1.5.0 (2026-06-10)
- **In the box formato corto**: `2x Coil Spring (SKU123) | 2x Rear Shock (SKU456)`
- **Part Sku**: Usa columna "Part Sku" para el numero de parte en in_the_box
- **OME sin SKU**: Cuando vendor es Old Man Emu/OME, no incluye numero de parte en in_the_box

### v1.4.0 (2026-06-10)
- **Sell without stock**: `Inventory Policy` cambiado a `continue` (siempre activo)
- **Producto físico**: `Requires Shipping` cambiado a `TRUE`
- **Handle nuevo formato**: `MARCA_SHOCK_ALTURA-INCH_LIFT-KIT_MODELO_AÑO` (ej: `dobinsons_ims_2.5-inch_lift-kit_gx550_24`)
- **Bilstein B8**: Si vendor es Bilstein, la marca en el handle es "Bilstein-B8"
- **Metafield de color**: Para vendor Dobinsons, usa columna "Color" → `custom.color`
- **Metafields de producto**: Formato cambiado de JSON a `;` separado (ej: `2 inch;2.5 inch;3 inch`)

### v1.3.0 (2026-06-10)
- **Metafields de producto**: `custom.height` (lista de alturas) y `custom.load` (lista de cargas)
- **Metafields de variante**: `custom.in_the_box`, `custom.lift_range`, `custom.shock_position`, `custom.shipping_ome_bilstein`, `custom.shipping_dobinsons`
- **Detección automática** de columnas "Pin Position for Install" y "Rear Lift"
- **Shipping automático**: asigna shipping según vendor (OME/Bilstein vs Dobinsons)

### v1.2.0 (2026-06-10)
- **Años abreviados en título**: "2024-2026" → "(24-26)", "2010-2024" → "(10-24)"

### v1.1.0 (2026-06-10)
- **Shock como diferenciador de producto**: Cada tipo de shock (IMS, MRR, Nitro, etc.) ahora genera un producto separado en Shopify
- **Título mejorado**: Incluye nombre del shock y rango de alturas (ej: "Dobinsons IMS Lift Kit for Lexus GX550 (2024) - 2-3 inch")
- **Orden de variantes**: Standard → Medium → Heavy (en lugar de orden alfabético)
- **Detección automática de columna Shock**: Busca columnas llamadas "Shock" o "Shock Type"

### v1.0.0 (2026-06-10)
- Versión inicial
- Generación de Excel compatible con Matrixify
- 3 opciones de variante: Lift Setting + Front Load + Rear Load
- Detección automática de vendors, vehículos y columnas
- Comando NEW para productos nuevos
"""

st.set_page_config(
    page_title="Shopify Product Builder",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Shopify Product Builder")
st.caption(f"Versión {APP_VERSION}")
st.markdown("Genera archivos Excel compatibles con Matrixify para importar productos a Shopify")

with st.sidebar:
    st.header("⚙️ Configuración")
    
    tags = st.text_input(
        "Tags",
        value="Full Lift Kit, Liftkit",
        help="Tags separados por coma que se aplicarán a todos los productos"
    )
    
    status = st.selectbox(
        "Status",
        ["Draft", "Active", "Archived"],
        index=0,
        help="Estado inicial de los productos en Shopify"
    )
    
    product_type = st.text_input(
        "Product Type",
        value="Lift Kits",
        help="Tipo de producto en Shopify"
    )
    
    st.divider()
    
    with st.expander("📋 Changelog"):
        st.markdown(CHANGELOG)
    
    st.divider()
    st.markdown("### 📋 Instrucciones")
    st.markdown("""
    1. Sube tu archivo SuspensionConfigurator.xlsx
    2. Revisa el análisis automático
    3. Ajusta la configuración si es necesario
    4. Haz clic en "Generar Excel"
    5. Descarga el archivo y súbelo a Matrixify
    """)

uploaded_file = st.file_uploader(
    "Sube tu archivo SuspensionConfigurator.xlsx",
    type=["xlsx", "xls"],
    help="Archivo Excel con la configuración de suspensiones"
)

if uploaded_file is not None:
    try:
        with st.spinner("Analizando archivo..."):
            df = parse_input(uploaded_file)
            info = analyze_input(df)
        
        st.success(f"✅ Archivo cargado: {info['total_rows']} filas")
        
        with st.expander("📊 Análisis del archivo", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de filas", info['total_rows'])
                st.metric("Vehículos encontrados", len(info['vehicles']))
            
            with col2:
                st.metric("Vendors detectados", len(info['vendors']))
                if info['lift_col']:
                    st.success(f"Columna Lift: {info['lift_col']}")
                else:
                    st.warning("⚠️ Columna Lift no encontrada")
            
            with col3:
                if info['shock_col']:
                    st.success(f"Columna Shock: {info['shock_col']}")
                    st.metric("Tipos de shock", len(info['shocks']))
                else:
                    st.warning("⚠️ Columna Shock no encontrada")
                
                if info.get('pin_position_col'):
                    st.success(f"Columna Pin Position: {info['pin_position_col']}")
                else:
                    st.warning("⚠️ Columna Pin Position no encontrada")
                
                if info.get('rear_lift_col'):
                    st.success(f"Columna Rear Lift: {info['rear_lift_col']}")
                else:
                    st.warning("⚠️ Columna Rear Lift no encontrada")
                
                if info.get('color_col'):
                    st.success(f"Columna Color: {info['color_col']}")
                else:
                    st.info("ℹ️ Columna Color no encontrada (solo para Dobinsons)")
                
                if info.get('part_sku_col'):
                    st.success(f"Columna Part Sku: {info['part_sku_col']}")
                else:
                    st.warning("⚠️ Columna Part Sku no encontrada")
                
                if info.get('position_col'):
                    st.success(f"Columna Position: {info['position_col']}")
                else:
                    st.warning("⚠️ Columna Position no encontrada")
                
                if info.get('type_col'):
                    st.success(f"Columna Type: {info['type_col']}")
                else:
                    st.warning("⚠️ Columna Type no encontrada")
                
                if info['vehicles_without_data'] > 0:
                    st.warning(f"⚠️ {info['vehicles_without_data']} filas sin Make/Model")
            
            if info['vendors']:
                st.markdown("**Vendors:** " + ", ".join(info['vendors']))
            
            if info['shocks']:
                st.markdown("**Shocks:** " + ", ".join(info['shocks']))
            
            if info['vehicles']:
                st.markdown(f"**Vehículos:** {len(info['vehicles'])} únicos")
                with st.expander("Ver lista de vehículos"):
                    for v in info['vehicles'][:20]:
                        st.write(f"• {v.replace('|', ' ')}")
                    if len(info['vehicles']) > 20:
                        st.write(f"... y {len(info['vehicles']) - 20} más")
        
        st.divider()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            generate_btn = st.button("🚀 Generar Excel", type="primary", use_container_width=True)
        
        if generate_btn:
            with st.spinner("Generando archivo Excel..."):
                try:
                    output, summary, result_df = build_matrixify_excel(
                        df,
                        tags=tags,
                        status=status,
                        product_type=product_type,
                        lift_col=info['lift_col'],
                        shock_col=info['shock_col'],
                        pin_position_col=info['pin_position_col'],
                        rear_lift_col=info['rear_lift_col'],
                        color_col=info['color_col'],
                        part_sku_col=info['part_sku_col'],
                        position_col=info['position_col'],
                        type_col=info['type_col'],
                        qty_col=info['qty_col']
                    )
                    
                    st.success(f"✅ Generado exitosamente: {len(summary)} productos")
                    
                    total_variants = sum(s['variants'] for s in summary)
                    st.info(f"📦 Total de variantes: {total_variants}")
                    
                    st.download_button(
                        label="💾 Descargar Excel para Matrixify",
                        data=output,
                        file_name="matrixify_products.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                    
                    with st.expander("📋 Resumen de productos generados"):
                        summary_df = pd.DataFrame(summary)
                        st.dataframe(summary_df, use_container_width=True)
                    
                    with st.expander("🔍 Preview del Excel (primeras 10 filas)"):
                        st.dataframe(result_df.head(10), use_container_width=True)
                
                except Exception as e:
                    st.error(f"❌ Error al generar: {str(e)}")
                    st.exception(e)
    
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {str(e)}")
        st.exception(e)

else:
    st.info("👆 Sube un archivo Excel para comenzar")
    
    with st.expander("ℹ️ Formato esperado del archivo"):
        st.markdown("""
        El archivo debe contener las siguientes columnas:
        
        **Requeridas:**
        - `Make` - Marca del vehículo (ej: Toyota, Lexus)
        - `Model` - Modelo del vehículo (ej: 4Runner, GX550)
        - `Year` - Año del vehículo
        - `Brand` - Marca del producto (ej: Old Man Emu, Dobinsons)
        - `Part Name` - Nombre del componente
        - `Qty` o `Qty Customer` - Cantidad
        - `Parent Sku` - SKU del producto padre
        - `Total Price` - Precio total
        - `Front Load` - Carga frontal (Standard, Medium, Heavy, etc.)
        - `Rear Load` - Carga trasera (Standard, Medium, Heavy, etc.)
        
        **Opcionales:**
        - `Shock` / `Shock Type` - Tipo de shock (IMS, MRR, Nitro, etc.)
          - Cada tipo de shock genera un producto separado
        - `Lift Height` / `Height` / `Lift` - Altura del lift (2, 2.5, 3, etc.)
          - Si no está presente, se extraerá del Parent Sku
        
        **Ejemplo:**
        | Make | Model | Year | Brand | Shock | Part Name | Qty | Parent Sku | Total Price | Front Load | Rear Load | Height |
        |------|-------|------|-------|-------|-----------|-----|------------|-------------|------------|-----------|--------|
        | Toyota | 4Runner | 2020 | Old Man Emu | Nitro | Coil Spring | 2 | OME4R-2STC | 1147.70 | Standard | Heavy | 2 |
        """)
