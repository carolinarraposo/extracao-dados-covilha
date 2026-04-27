import os
import time
import requests
import feedparser
import pandas as pd
import trafilatura

from newspaper import Article
from googlenewsdecoder import new_decoderv1
from datetime import datetime, timedelta

# ================================
# Configuração
# ================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

CSV_FILE = os.path.join(RAW_DIR, "news_posts.csv")
JSON_FILE = os.path.join(RAW_DIR, "news_posts.json")

QUERY_BASE = "covilhã"
# True = extrai histórico desde janeiro 2025
# False = extrai só notícias recentes
BACKFILL = False

DAYS_RECENT = 7

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def obter_periodos():
    if BACKFILL:
        return [
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
            ("2026-03-01", "2026-03-31"),
            ("2026-04-01", datetime.today().strftime("%Y-%m-%d")),
        ]

    hoje = datetime.today()
    inicio = hoje - timedelta(days=DAYS_RECENT)

    return [
        (inicio.strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d"))
    ]


def carregar_dados_existentes():
    if os.path.exists(JSON_FILE):
        return pd.read_json(JSON_FILE, orient="records", encoding="utf-8")

    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)

    return pd.DataFrame()


def extrair_texto(url):
    try:
        article = Article(url, language="pt")
        article.download()
        article.parse()

        texto = article.text.strip()

        if len(texto) > 200:
            return texto

    except Exception:
        pass

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code == 200:
            texto = trafilatura.extract(response.text)

            if texto:
                return texto.strip()

    except Exception:
        pass

    return ""


def extrair_noticias():
    df_antigo = carregar_dados_existentes()
    links_existentes = set()

    if not df_antigo.empty and "link" in df_antigo.columns:
        links_existentes = set(df_antigo["link"].dropna().tolist())

    novas_noticias = []
    periodos = obter_periodos()

    print(f"Modo BACKFILL: {BACKFILL}")
    print(f"Períodos a pesquisar: {periodos}")

    for inicio, fim in periodos:
        print(f"\nNotícias: {inicio} até {fim}")

        query_temporal = f"{QUERY_BASE} after:{inicio} before:{fim}"
        encoded_query = query_temporal.replace(" ", "+")

        rss_url = (
            f"https://news.google.com/rss/search?"
            f"q={encoded_query}&hl=pt-PT&gl=PT&ceid=PT:pt"
        )

        feed = feedparser.parse(rss_url)

        print(f"Entradas encontradas: {len(feed.entries)}")

        for entry in feed.entries:
            google_link = entry.link

            if google_link in links_existentes:
                continue

            print(f"A processar: {entry.title[:80]}...")

            try:
                decoded = new_decoderv1(google_link)
                real_url = (
                    decoded.get("decoded_url")
                    if isinstance(decoded, dict)
                    else str(decoded)
                )

                noticia = {
                    "source": "news",
                    "platform_id": google_link,
                    "title": entry.title,
                    "link": google_link,
                    "url": real_url,
                    "created_at": entry.published,
                    "text": extrair_texto(real_url),
                    "metrics": {},
                    "comments": []
                }

                novas_noticias.append(noticia)
                links_existentes.add(google_link)

                time.sleep(0.5)

            except Exception as e:
                print(f"Erro ao processar notícia: {e}")

    return df_antigo, novas_noticias


def guardar_resultados(df_antigo, novas_noticias):
    if not novas_noticias:
        print("News: nenhuma notícia nova encontrada.")
        return

    df_novo = pd.DataFrame(novas_noticias)
    df_final = pd.concat([df_antigo, df_novo], ignore_index=True)

    if "link" in df_final.columns:
        df_final = df_final.drop_duplicates(subset=["link"])

    if "created_at" in df_final.columns:
        df_final["date_dt"] = pd.to_datetime(
            df_final["created_at"],
            errors="coerce",
            utc=True
        )

        df_final = df_final.sort_values(
            by="date_dt",
            ascending=False
        )

        df_final = df_final.drop(columns=["date_dt"])

    df_final.to_csv(CSV_FILE, index=False, encoding="utf-8")
    df_final.to_json(
        JSON_FILE,
        orient="records",
        force_ascii=False,
        indent=4
    )

    print(f"\nNews: {len(novas_noticias)} novas notícias guardadas.")
    print(f"Total acumulado: {len(df_final)}")


def run():
    df_antigo, novas_noticias = extrair_noticias()
    guardar_resultados(df_antigo, novas_noticias)


if __name__ == "__main__":
    run()