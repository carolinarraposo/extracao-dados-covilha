import feedparser
import pandas as pd
from newspaper import Article
import time
import os

# 1. Configurações Iniciais
file_name = "news_tests.csv"
query = "covilhã"
max_news = 100
rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=pt-PT&gl=PT&ceid=PT:pt"

# 2. Carregar links já existentes para evitar re-extração
links_existentes = set()
if os.path.exists(file_name):
    df_antigo = pd.read_csv(file_name)
    links_existentes = set(df_antigo['link'].tolist())
    print(f"Memória carregada: {len(links_existentes)} notícias já conhecidas.")

# 3. Obter o Feed
print("A aceder ao Google News...")
feed = feedparser.parse(rss_url)
novas_noticias = []

# 4. Loop de Extração Inteligente
for entry in feed.entries[:max_news]:
    link = entry.link
    
    # SALTAR se o link já estiver no nosso histórico
    if link in links_existentes:
        continue 

    print("Nova notícia encontrada:", entry.title)
    
    try:
        article = Article(link)
        article.download()
        article.parse()
        text = article.text
        
        novas_noticias.append({
            "title": entry.title,
            "link": link,
            "date": entry.published
        })
        
        # Pausa ética para não ser bloqueado
        time.sleep(2)
        
    except Exception as e:
        print(f"Erro ao extrair {link}: {e}")

# 5. Atualizar o ficheiro
if novas_noticias:
    df_novo = pd.DataFrame(novas_noticias)
    
    # Se o ficheiro já existia, fazemos o "append" (anexar)
    if os.path.exists(file_name):
        df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
    else:
        df_final = df_novo
        
    df_final.to_csv(file_name, index=False, encoding="utf-8")
    print(f"\nSucesso! Foram adicionadas {len(novas_noticias)} novas notícias.")
else:
    print("\nNão foram encontradas notícias novas desde a última extração.")