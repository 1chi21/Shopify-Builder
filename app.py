import streamlit as st
import pandas as pd
from builder import parse_input, analyze_input, build_matrixify_excel

APP_VERSION = "1.1.0"

CHANGELOG = """
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
