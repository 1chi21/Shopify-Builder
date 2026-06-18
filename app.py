import streamlit as st
import pandas as pd
from builder import parse_input, analyze_input, build_matrixify_excel, build_seo_gmc_only

APP_VERSION = "1.8.7"

CHANGELOG = """
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

# Sistema de pestañas
tab1, tab2 = st.tabs(["🆕 Crear Productos", "📝 SEO & GMC Titles"])

with tab1:
    st.header("Crear Productos Nuevos")
    st.markdown("Genera productos nuevos en Shopify con todas las variantes y metafields")
    
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
                    
                    # Mostrar columnas para SEO/GMC titles
                    if info.get('gen_col'):
                        st.success(f"Columna Gen: {info['gen_col']}")
                    else:
                        st.info("ℹ️ Columna Gen no encontrada (para SEO/GMC titles)")
                    
                    if info.get('engine_col'):
                        st.success(f"Columna Engine: {info['engine_col']}")
                    else:
                        st.info("ℹ️ Columna Engine no encontrada (para GMC titles)")
                    
                    if info.get('drive_col'):
                        st.success(f"Columna Drive: {info['drive_col']}")
                    else:
                        st.info("ℹ️ Columna Drive no encontrada (para GMC titles)")
                    
                    if info.get('trim_col'):
                        st.success(f"Columna Trim: {info['trim_col']}")
                    else:
                        st.info("ℹ️ Columna Trim no encontrada (para SEO/GMC titles)")
                    
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
                            qty_col=info['qty_col'],
                            gen_col=info.get('gen_col'),
                            engine_col=info.get('engine_col'),
                            drive_col=info.get('drive_col'),
                            trim_col=info.get('trim_col')
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

with tab2:
    st.header("Actualizar SEO & GMC Titles")
    st.markdown("Genera solo los metafields SEO Title y GMC Title para productos existentes en Shopify")
    
    st.info("ℹ️ Esta pestaña es para actualizar kits que YA existen en Shopify. Solo genera los campos necesarios para actualizar los títulos SEO y GMC.")
    
    uploaded_file_seo = st.file_uploader(
        "Sube tu archivo SuspensionConfigurator.xlsx",
        type=["xlsx", "xls"],
        help="Archivo Excel con la configuración de suspensiones",
        key="seo_uploader"
    )
    
    if uploaded_file_seo is not None:
        try:
            with st.spinner("Analizando archivo..."):
                df_seo = parse_input(uploaded_file_seo)
                info_seo = analyze_input(df_seo)
            
            st.success(f"✅ Archivo cargado: {info_seo['total_rows']} filas")
            
            with st.expander("📊 Análisis del archivo", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de filas", info_seo['total_rows'])
                    st.metric("Vehículos encontrados", len(info_seo['vehicles']))
                
                with col2:
                    st.metric("Vendors detectados", len(info_seo['vendors']))
                    if info_seo['lift_col']:
                        st.success(f"Columna Lift: {info_seo['lift_col']}")
                    else:
                        st.warning("⚠️ Columna Lift no encontrada")
                    
                    if info_seo['shock_col']:
                        st.success(f"Columna Shock: {info_seo['shock_col']}")
                    else:
                        st.warning("⚠️ Columna Shock no encontrada")
                
                with col3:
                    if info_seo.get('gen_col'):
                        st.success(f"Columna Gen: {info_seo['gen_col']}")
                    else:
                        st.warning("⚠️ Columna Gen no encontrada")
                    
                    if info_seo.get('engine_col'):
                        st.success(f"Columna Engine: {info_seo['engine_col']}")
                    else:
                        st.info("ℹ️ Columna Engine no encontrada")
                    
                    if info_seo.get('drive_col'):
                        st.success(f"Columna Drive: {info_seo['drive_col']}")
                    else:
                        st.info("ℹ️ Columna Drive no encontrada")
                    
                    if info_seo.get('trim_col'):
                        st.success(f"Columna Trim: {info_seo['trim_col']}")
                    else:
                        st.info("ℹ️ Columna Trim no encontrada")
                    
                    if info_seo.get('id_col'):
                        st.success(f"Columna ID: {info_seo['id_col']} (se usará para agrupar SEO Titles)")
                    else:
                        st.info("ℹ️ Columna ID no encontrada (SEO Titles se agruparán por vehículo)")
            
            st.divider()
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                generate_seo_btn = st.button("🚀 Generar SEO & GMC Titles", type="primary", use_container_width=True, key="seo_generate")
            
            if generate_seo_btn:
                with st.spinner("Generando títulos SEO y GMC..."):
                    try:
                        output_seo, summary_seo, result_df_seo = build_seo_gmc_only(
                            df_seo,
                            lift_col=info_seo['lift_col'],
                            shock_col=info_seo['shock_col'],
                            gen_col=info_seo.get('gen_col'),
                            engine_col=info_seo.get('engine_col'),
                            drive_col=info_seo.get('drive_col'),
                            trim_col=info_seo.get('trim_col'),
                            type_col=info_seo.get('type_col'),
                            id_col=info_seo.get('id_col')
                        )
                        
                        st.success(f"✅ Generado exitosamente: {len(summary_seo)} productos")
                        
                        total_variants_seo = sum(s['variants'] for s in summary_seo)
                        st.info(f"📦 Total de variantes: {total_variants_seo}")
                        
                        # Verificar límites de caracteres
                        seo_over_limit = [s for s in summary_seo if s['seo_chars'] > 70]
                        if seo_over_limit:
                            st.warning(f"⚠️ {len(seo_over_limit)} SEO Titles superan los 70 caracteres")
                            with st.expander("Ver títulos que superan el límite"):
                                for s in seo_over_limit:
                                    st.write(f"**{s['handle']}** ({s['seo_chars']} chars)")
                                    st.write(f"`{s['seo_title']}`")
                        
                        st.download_button(
                            label="💾 Descargar Excel para Matrixify",
                            data=output_seo,
                            file_name="matrixify_seo_gmc_update.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                            use_container_width=True,
                            key="seo_download"
                        )
                        
                        with st.expander("📋 Resumen de títulos generados"):
                            summary_df_seo = pd.DataFrame(summary_seo)
                            st.dataframe(summary_df_seo, use_container_width=True)
                        
                        with st.expander("🔍 Preview del Excel (primeras 10 filas)"):
                            st.dataframe(result_df_seo.head(10), use_container_width=True)
                    
                    except Exception as e:
                        st.error(f"❌ Error al generar: {str(e)}")
                        st.exception(e)
        
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {str(e)}")
            st.exception(e)
    
    else:
        st.info("👆 Sube un archivo Excel para generar los títulos SEO y GMC")
        
        with st.expander("ℹ️ ¿Cómo funciona?"):
            st.markdown("""
            **Esta pestaña genera un archivo Excel con SOLO los campos necesarios para actualizar:**
            
            - `Handle` - Identificador del producto en Shopify
            - `Command` - Siempre "UPDATE" para actualizar productos existentes
            - `Metafield: title_tag [string]` - SEO Title (máximo 70 caracteres)
            - `Variant SKU` - Identificador de la variante
            - `Variant Metafield: custom.gmc_title [single_line_text_field]` - GMC Title (máximo 150 caracteres)
            
            **Pasos:**
            1. Sube tu archivo SuspensionConfigurator.xlsx (el mismo que usaste para crear los productos)
            2. La app genera los títulos SEO y GMC según las reglas de Carlos
            3. Descarga el archivo Excel
            4. Súbelo a Matrixify para actualizar solo esos campos en Shopify
            
            **Nota:** Esto NO crea productos nuevos, solo actualiza los títulos SEO y GMC de productos existentes.
            """)
