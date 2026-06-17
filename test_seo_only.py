import sys
sys.path.insert(0, '.')
from builder import parse_input, analyze_input, build_seo_gmc_only

# Leer archivo de entrada
df = parse_input('../4runner tacoma ome.xlsx')
info = analyze_input(df)

print(f"=== Test build_seo_gmc_only ===")
print(f"Columna lift detectada: {info['lift_col']}")
print(f"Columna shock detectada: {info['shock_col']}")
print(f"Columna gen detectada: {info.get('gen_col')}")
print()

# Procesar solo títulos SEO/GMC
output, summary, result_df = build_seo_gmc_only(
    df,
    lift_col=info['lift_col'],
    shock_col=info['shock_col'],
    gen_col=info.get('gen_col'),
    engine_col=info.get('engine_col'),
    drive_col=info.get('drive_col'),
    trim_col=info.get('trim_col'),
    type_col=info.get('type_col')
)

print(f"Productos procesados: {len(summary)}")
print()
print("Primeras 10 filas del resultado:")
print(result_df.head(10).to_string())
print()
print("Columnas del resultado:")
print(list(result_df.columns))
print()
print("Ejemplos de SEO Title:")
for s in summary[:3]:
    print(f"  {s['handle']}: {s['seo_title']} ({s['seo_chars']} chars)")
print()
print("Verificación de límites:")
over_limit = [s for s in summary if s['seo_chars'] > 70]
print(f"  SEO Titles que superan 70 chars: {len(over_limit)}")
if over_limit:
    for s in over_limit[:3]:
        print(f"    {s['handle']}: {s['seo_chars']} chars")
