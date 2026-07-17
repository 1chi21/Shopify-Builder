import streamlit as st
import pandas as pd
from builder import parse_input, analyze_input, build_matrixify_excel, build_seo_gmc_only, FRONT_LOAD_MAP, REAR_LOAD_MAP, map_option

APP_VERSION = "1.11.1"

CHANGELOG = """
### v1.11.1 (2026-07-17)
- **Regla Gen para Bilstein**: Si el Gen tiene una generacion (ej: "5th Gen", "5thGen") se muestra en el titulo. Si no la tiene (es un año/rango como "14-18", "19-ON", "2010-2024") se omite para evitar duplicar con el year del final. Aplica tanto a SEO como a GMC.
- **Regex de año mejorada en get_generation**: Ahora tambien matchea sufijos "-ON" (year onwards) en el Gen, no solo rangos numericos como "14-18" o "2010-2016".
- **DEPRECATED**: `get_generation_bilstein` ya no se usa en el flujo principal (las funciones Bilstein ahora usan `get_generation` directamente).

### v1.11.0 (2026-07-17)
- **Arquitectura por marca (OME vs Bilstein)**: Se detecta la marca del producto (columna `Brand`) y se aplican reglas distintas para cada una.
- **Reglas Bilstein implementadas**:
  - `is_bilstein(brand)` - detecta marca Bilstein (case-insensitive)
  - `get_bilstein_shocks(vdf, shock_col, position_col)` - extrae front/rear shocks segun Position (Front/Rear)
  - `format_bilstein_shocks(front, rear)` - formatea "front/rear", "front" si son iguales, o solo el existente
  - `get_bilstein_shock_tech(front, rear)` - mapea shock a tecnologia (5100→Adjustable/Monotube, 5160→-/Remote Reservoir, 6112→Adjustable Coilover/-, 8100→-/Bypass DSA, 8112→Zone Control/-)
  - `get_generation_bilstein(gen)` - para Bilstein, NO filtra años del Gen (muestra "14-18" tal cual)
  - `is_bilstein_assembled(vdf)` - detecta "-ASS" en SKU o Assembly="ASS"
  - `build_bilstein_seo_title(...)` - formato: `Bilstein {shocks} {model} {gen} {internal_type} {height}" ({year})`
  - `build_bilstein_gmc_title(...)` - formato: `... {front_tech}, {rear_tech}` con prefijo "Front" solo en el front tech. Sin "Suspension Upgrade" (diferente de OME)
- **Tabla `BILSTEIN_SHOCK_TECH`** agregada a `title_rules.py` con el mapeo de shock a tecnologia front/rear.
- **Fallback de Height mejorado**: Ahora tambien dispara cuando el valor es solo un año de 4 digitos (ej: "2026" de datetime), no solo cuando esta vacio. Extrae el height real del SKU.
- **Ruteo en builder.py**: `build_matrixify_excel` y `build_seo_gmc_only` ahora detectan Bilstein y llaman a las funciones correspondientes.
- **Aislamiento**: Productos OME siguen usando las reglas existentes. Productos de otras marcas (Toyota, Dobinsons, etc.) usan las reglas OME por default.
- **Limite de caracteres**: Mismo que OME (GMC 150 con fallback, SEO sin limite).

### v1.10.1 (2026-06-22)
- **Regla multi-modelo aplicada al título**: `build_seo_title` y `build_gmc_title` ahora usan `get_model_for_title()` que aplica la regla de Carlos:
  - **Default (3+ modelos)**: usa SOLO la marca (ej: `"BroncoBase,BigBend,OuterBanks,Wildtrack(2.7engine)"` → `"Bronco"`)
  - **Especial (<3 modelos)**: deja el modelo completo (ej: `"BroncoBlackDiamond,Badlands"` → tal cual)
- **Nuevo helper `extract_brand_from_model`**: extrae la marca de modelos concatenados usando una lista de marcas conocidas (Bronco, Hilux, LandCruiser, 4Runner, etc.)

### v1.10.0 (2026-06-22)
- **Land Cruiser GMC**: Nuevo helper `get_landcruiser_abbreviation()` que extrae `LC{n}` del modelo (ej: `"LandCruiser250"` → `LC250`, `"100 Series Land Cruiser"` → `LC100`). Se agrega antes de "Suspension Upgrade" en el GMC title (ej: `... OME Monotube Shocks LC250 Suspension Upgrade`).
- **Non Rubicon filtrado**: Nuevo helper `is_non_rubicon()`. Cuando el trim es "Non Rubicon" NO se agrega al título (es la versión por defecto de Rubicon). Solo "Rubicon" (u otros trims válidos) aparecen en el título.
- **Multi-modelo count helper**: Nuevo helper `count_models_in_string()` que cuenta modelos separados por coma, slash, o "y" (ej: `"Hilux REVO/ROCCO/SR5"` → 3). Helper disponible para identificar default vs caso especial.
- **Aislamiento**: Reglas Land Cruiser y Non Rubicon solo aplican cuando el modelo/trim matchea. Productos no-Land Cruiser o con otro trim no se ven afectados.

### v1.9.6 (2026-06-22)

### v1.9.5 (2026-06-22)
- **Bug fix rango de años 2 dígitos**: `get_generation` ahora también filtra rangos de años con 2 dígitos (ej: `"14-18"`, `"10-16"`) además de los de 4 dígitos. El regex cambió de `^\d{4}(-\d{2,4})?$` a `^\d{2,4}(-\d{2,4})?$` para cubrir ambos formatos.
- **Aislamiento**: Productos con Gen válido (`"5thGen"`, `"4thGen"`, etc.) siguen funcionando.

### v1.9.4 (2026-06-22)
- **SEO Title sin límite para todos**: Se removió completamente el límite de 70 caracteres en SEO Title. Ya no se agrega `[EXCEDE 70 CHARS]` para NINGÚN producto (antes solo Assembly lo tenía sin límite).
- **Aislamiento**: GMC Title mantiene su límite de 150 caracteres con fallbacks progresivos (Suspension Upgrade → tech description para Assembly).

### v1.9.3 (2026-06-22)
- **Bug fix año duplicado en títulos**: `get_generation` ahora ignora valores que son años o rangos de años (ej: `"2018"`, `"2010-2016"`, `"2010-16"`) además de datetimes. Esto evita que el año aparezca duplicado en SEO/GMC Title (una vez en la posición de Gen y otra al final entre paréntesis).
- **Aislamiento**: Solo afecta el campo Gen. Valores válidos como `"5thGen"`, `"4thGen"`, `"100 Series"` siguen funcionando normalmente.

### v1.9.2 (2026-06-22)
- **Bug fix datetime persistente**: Ademas de detectar objetos `datetime`/`pd.Timestamp`, `clean_str` ahora tambien detecta **strings con formato datetime** tipo `"2018-07-01 00:00:00"` o `"2018-07-01"` y extrae el año (ej: `"2018-07-01 00:00:00"` → `"2018"`). Esto cubre el caso donde el valor llega como string y no como objeto datetime.
- **Limpieza a nivel de columna**: Las columnas `Gen`, `Engine`, `Drive`, `Trim` y `Shock` ahora se limpian con `clean_str` a nivel de columna en `analyze_input` y `build_matrixify_excel` (antes solo se limpiaban `Make/Model/Year/Brand`). Esto garantiza que todos los valores pasen por la limpieza, no solo los de la primera fila.
- **Aislamiento**: El fix aplica a cualquier campo que pase por `clean_str` en cualquier tab.

### v1.9.1 (2026-06-22)
- **Bug fix datetime en títulos**: `clean_str` ahora detecta valores `datetime`/`pd.Timestamp` y los convierte a año como string (ej: `2018-07-01 00:00:00` → `2018`). Esto evita que strings datetime completos generados por Excel (cuando formatea celdas de año como fecha) terminen en los títulos SEO/GMC.
- **Aislamiento**: Aplica a cualquier campo que pase por `clean_str` (Make, Model, Year, Brand, Gen, Engine, Drive, Trim, Shock, etc.)

### v1.9.0 (2026-06-22)
- **Assembly en SEO Title**: Productos con `-ASS` en el SKU ahora muestran `w/ Strut Assembly` justo después de `Lift Kit` y antes de la altura y los años (ej: `OME BP-51 5th Gen 4Runner Lift Kit w/ Strut Assembly 2-3" (2010-2024)`)
- **Assembly en GMC Title**: Misma inserción `w/ Strut Assembly` en GMC Title (nivel variante)
- **SEO Title sin límite para Assembly**: Para productos Assembly, el límite de 70 caracteres ya NO se aplica (no se agrega marcador `[EXCEDE]`)
- **GMC Title Assembly con fallback agresivo**: Para productos Assembly, si el título supera 150 chars: primero se elimina `Suspension Upgrade` y como último recurso se elimina la tecnología del shock (Monotube/Bypass/Twin Tube Shocks) y su arquitectura (ej: Remote Reservoir, Adjustable Coilover)
- **Aislamiento**: Productos no-Assembly mantienen el comportamiento anterior sin cambios

### v1.8.11 (2026-06-18)
- **Editor de opciones de variantes**: Nueva seccion en Tab 1 despues del analisis. Permite editar el texto de Option2/Option3 Value (la capacidad de carga tipo "Standard (Up to 50 lbs)") para cada valor de Front Load y Rear Load detectado. Util cuando no todos los productos tienen las mismas capacidades.
- **Inputs pre-llenados**: Cada input arranca con el valor mapeado por defecto; si lo editas, se usa el nuevo texto en el output.
- **Valores no mapeados**: Si el archivo tiene un valor de carga que no esta en el map, se muestra un input vacio para que lo llenes manualmente.
- **Backward compatible**: Si no tocas nada, se usan los valores del map (comportamiento previo). Nuevo parametro `option_value_overrides` en `build_matrixify_excel` con default `None`.
- **Sort intacto**: El orden de variantes sigue basado en los valores del map, no en el texto override (los overrides son cosmeticos).

### v1.8.10 (2026-06-18)
- **Bug fix orden de variantes**: `sort_variants` ahora extrae el primer número del rango de altura (ej: "4-6" → 4, "2-2.5" → 2) en lugar de hacer `float()` directo que fallaba con rangos. Esto corrige el orden ascendente de variantes para productos con alturas-rango.
- **Bug fix altura vacía (nan)**: Cuando la columna Height tiene valores inválidos (datetime, NaN) en el input, la app ahora extrae la altura del Parent Sku como fallback (patrón `-{shock}-{altura}LEV$`). Esto corrige el problema donde variantes 4-6 aparecían con Option1="nan" en archivos de Bilstein Silverado.
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

            # Editor de texto de Option2/Option3 Value (opcional, despues del analisis)
            with st.expander("✏️ Opciones de variantes (opcional)", expanded=True):
                st.caption("Edita el texto de las opciones Front Load / Rear Load si cambia la capacidad. Si dejas el default, se usa el mapeo estandar.")

                def compute_override_keys(series, mapping):
                    """Devuelve dict {key: (label, default_value)} para los inputs.
                    Mapeados: key=mapped, default=mapped. No mapeados: key=raw, default=''."""
                    result = {}
                    for raw in series.dropna().unique():
                        raw_s = str(raw).strip()
                        if not raw_s or raw_s.lower() in ("nan", "none", "n/a", ""):
                            continue
                        mapped = map_option(raw, mapping, default="")
                        if mapped:
                            result[mapped] = (mapped, mapped)
                        else:
                            result[raw_s] = (raw_s, "")
                    return result

                front_keys = compute_override_keys(df["Front Load"], FRONT_LOAD_MAP) if "Front Load" in df.columns else {}
                rear_keys = compute_override_keys(df["Rear Load"], REAR_LOAD_MAP) if "Rear Load" in df.columns else {}

                option_value_overrides = {"front": {}, "rear": {}}

                if front_keys or rear_keys:
                    col_f, col_r = st.columns(2)
                    with col_f:
                        st.markdown("**Front Load**")
                        for key, (label, default) in front_keys.items():
                            val = st.text_input(label, value=default, key=f"of_{key}")
                            if val and val.strip():
                                option_value_overrides["front"][key] = val.strip()
                    with col_r:
                        st.markdown("**Rear Load**")
                        for key, (label, default) in rear_keys.items():
                            val = st.text_input(label, value=default, key=f"or_{key}")
                            if val and val.strip():
                                option_value_overrides["rear"][key] = val.strip()
                else:
                    st.info("No se detectaron valores de Front Load / Rear Load en el archivo.")

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
                            trim_col=info.get('trim_col'),
                            option_value_overrides=option_value_overrides
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
