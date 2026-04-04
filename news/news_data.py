import feedparser
import pandas as pd
from newspaper import Article
import time
import os
import requests
import trafilatura
from googlenewsdecoder import new_decoderv1
from datetime import datetime

# ================================
# 1. Configurações
# ================================

FILE_NAME_CSV = "news_tests1.csv"
FILE_NAME_JSON = "news_tests1.json"
QUERY_BASE = "covilhã"

# Lista de meses para iterar (Desde Janeiro 2025 até Março 2026)
# Formato: (Data Início, Data Fim)
PERIODOS = [
    ("2025-01-01", "2025-01-31"),
    ("2025-02-01", "2025-02-28"),
    ("2025-03-01", "2025-03-31"),
    ("2025-04-01", "2025-04-30"),
    ("2025-05-01", "2025-05-31"),
    ("2025-06-01", "2025-06-30"),
    ("2025-07-01", "2025-07-31"),
    ("2025-08-01", "2025-08-31"),
    ("2025-09-01", "2025-09-30"),
    ("2025-10-01", "2025-10-31"),
    ("2025-11-01", "2025-11-30"),
    ("2025-12-01", "2025-12-31"),
    ("2026-01-01", "2026-01-31"),
    ("2026-02-01", "2026-02-28"),
    ("2026-03-01", "2026-03-31"), # Mês atual
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ================================
# 2. Carregar memória
# ================================

links_existentes = set()
df_antigo = pd.DataFrame()

if os.path.exists(FILE_NAME_JSON):
    df_antigo = pd.read_json(FILE_NAME_JSON, orient="records", encoding="utf-8")
elif os.path.exists(FILE_NAME_CSV):
    df_antigo = pd.read_csv(FILE_NAME_CSV)

if not df_antigo.empty:
    links_existentes = set(df_antigo["link"].tolist())
    print(f"Memória carregada: {len(links_existentes)} notícias")

# ================================
# 3. Funções de Apoio
# ================================

def extrair_texto(url):
    texto = ""
    try:
        article = Article(url, language="pt")
        article.download()
        article.parse()
        texto = article.text.strip()
        if len(texto) > 200: return texto
    except: pass

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            res = trafilatura.extract(r.text)
            if res: return res.strip()
    except: pass
    return ""

# ================================
# 4. Loop Principal por Períodos
# ================================

novas_noticias = []

for inicio, fim in PERIODOS:
    print(f"\n--- PESQUISANDO PERÍODO: {inicio} até {fim} ---")
    
    # Criar QUERY com operadores temporais
    query_temporal = f"{QUERY_BASE} after:{inicio} before:{fim}"
    encoded_query = query_temporal.replace(' ', '+')
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=pt-PT&gl=PT&ceid=PT:pt"
    
    feed = feedparser.parse(rss_url)
    print(f"Encontradas {len(feed.entries)} entradas neste período.")

    for entry in feed.entries:
        google_link = entry.link
        
        # SALTAR DUPLICADOS
        if google_link in links_existentes:
            continue

        print(f"Novo: {entry.title[:50]}...")

        try:
            decoded = new_decoderv1(google_link)
            real_url = decoded.get("decoded_url") if isinstance(decoded, dict) else str(decoded)
            
            texto = extrair_texto(real_url)
            
            noticia = {
                "title": entry.title,
                "link": google_link,
                "real_url": real_url,
                "date": entry.published,
                "text": texto,
            }
            novas_noticias.append(noticia)
            links_existentes.add(google_link) # Adiciona à memória imediata
            
            time.sleep(2) # Pausa ética

        except Exception as e:
            print(f"Erro ao processar: {e}")

# ================================
# 5. Guardar Resultados
# ================================

if novas_noticias:
    df_novo = pd.DataFrame(novas_noticias)
    df_final = pd.concat([df_antigo, df_novo], ignore_index=True)

    # Limpeza e ordenação
    df_final["date_dt"] = pd.to_datetime(df_final["date"], errors="coerce", utc=True)
    df_final = df_final.sort_values(by="date_dt", ascending=False)
    df_final = df_final.drop(columns=["date_dt"]).drop_duplicates(subset=["link"])

    df_final.to_csv(FILE_NAME_CSV, index=False, encoding="utf-8")
    df_final.to_json(FILE_NAME_JSON, orient="records", force_ascii=False, indent=4)

    print(f"\nFinalizado! Adicionadas {len(novas_noticias)} novas notícias.")
else:
    print("\nNenhuma notícia nova encontrada em todos os períodos pesquisados.")