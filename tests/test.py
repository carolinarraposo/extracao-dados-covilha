import pandas as pd
import os

files = ["news_tests1.csv", "news_tests1.json"]

for f in files:
    if not os.path.exists(f):
        print(f"--- Ficheiro {f} não encontrado ---")
        continue
    
    # Carregar o ficheiro conforme a extensão
    df = pd.read_json(f, orient="records") if f.endswith('.json') else pd.read_csv(f)
    
    total = len(df)
    # Verificar duplicados baseados na coluna 'link'
    duplicados = df.duplicated(subset=['link']).sum()
    
    print(f"--- Diagnóstico: {f} ---")
    print(f"Total de registos: {total}")
    print(f"Links duplicados encontrados: {duplicados}")
    
    if duplicados > 0:
        print(f"Dica: Use df.drop_duplicates(subset=['link']) para limpar.")
    print("-" * 30)

# Verificação Cruzada (Se os dois ficheiros têm o mesmo conteúdo)
if os.path.exists(files[0]) and os.path.exists(files[1]):
    df_csv = pd.read_csv(files[0])
    df_json = pd.read_json(files[1], orient="records")
    
    if len(df_csv) != len(df_json):
        print(f"Atenção: Os ficheiros têm tamanhos diferentes! (CSV: {len(df_csv)} | JSON: {len(df_json)})")
    else:
        print("Sincronização: Ambos os ficheiros têm o mesmo número de notícias.")