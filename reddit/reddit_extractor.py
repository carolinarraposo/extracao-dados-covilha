import os
import praw
import pandas as pd
import time
import json
from datetime import datetime, timezone
import re
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

LAST_RUN_FILE = 'last_run_reddit.json'

def carregar_ultimo_timestamp():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            return json.load(f).get('ultimo_post')
    return None

def guardar_ultimo_timestamp(timestamp):
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump({'ultimo_post': timestamp}, f)

def clean_text(text):
    if text:
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\w\s.,!?]', '', text)
    return text

def extrair_post(post):
    post.comments.replace_more(limit=0)
    comments_list = []
    for comment in post.comments.list():
        comments_list.append({
            "Autor": comment.author.name if comment.author else "Deleted",
            "Texto": clean_text(comment.body),
            "Upvotes": comment.score
        })
    return {
        "Título": post.title,
        "Autor": post.author.name if post.author else "Deleted",
        "Texto": clean_text(post.selftext),
        "Upvotes": post.score,
        "Total Comentários": post.num_comments,
        "Conteudo_Comentarios": comments_list,
        "Data": datetime.fromtimestamp(post.created_utc, timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        "URL": post.url,
        "timestamp": post.created_utc  # guardamos para comparação
    }

def extrair_posts_novos(geradores):
    ultimo_timestamp = carregar_ultimo_timestamp()
    posts_novos = []
    novo_mais_recente = None

    if ultimo_timestamp:
        print(f"A buscar posts mais recentes que: {datetime.fromtimestamp(ultimo_timestamp, timezone.utc)}")
    else:
        print("Primeira execução — a buscar todos os posts disponíveis")

    for gerador in geradores:
        for post in gerador:
            # Guarda o timestamp do post mais recente
            if novo_mais_recente is None or post.created_utc > novo_mais_recente:
                novo_mais_recente = post.created_utc

            # Ignora posts já recolhidos
            if ultimo_timestamp and post.created_utc <= ultimo_timestamp:
                continue

            try:
                dados = extrair_post(post)
                posts_novos.append(dados)
                print(f"Extraído: {post.title[:60]}...")
            except Exception as e:
                print(f"Erro ao processar post {post.url}: {e}")

            time.sleep(0.5)

    if novo_mais_recente:
        guardar_ultimo_timestamp(novo_mais_recente)
        print(f"Timestamp atualizado para: {datetime.fromtimestamp(novo_mais_recente, timezone.utc)}")

    return posts_novos

# Execução
subreddit = reddit.subreddit("covilha")
geradores = [
    subreddit.hot(limit=500),
    subreddit.controversial(time_filter="month", limit=1000)
]

posts_novos = extrair_posts_novos(geradores)

if not posts_novos:
    print("Nenhum post novo encontrado.")
else:
    # Remove o campo auxiliar antes de guardar
    for p in posts_novos:
        p.pop("timestamp", None)

    # Append ao JSON existente
    existentes = []
    if os.path.exists('reddit_posts.json'):
        with open('reddit_posts.json', 'r', encoding='utf-8') as f:
            existentes = json.load(f)

    todos = posts_novos + existentes
    with open('reddit_posts.json', 'w', encoding='utf-8') as f:
        json.dump(todos, f, ensure_ascii=False, indent=4)

    # Remove duplicados e guarda o ficheiro limpo
    df = pd.DataFrame(todos)
    df = df.drop_duplicates(subset=["Título", "Autor", "URL"])

    df.to_json('reddit_posts_clean.json', orient="records", indent=4, force_ascii=False)

    print(f"\nTotal de posts novos: {len(posts_novos)}")
    print(f"Total acumulado (sem duplicados): {len(df)}")
    print(f"\nEstatísticas agregadas:")
    print(f"Média de upvotes por post: {df['Upvotes'].mean():.2f}")
    print(f"Média de comentários por post: {df['Total Comentários'].mean():.2f}")
    print(f"Maior número de upvotes: {df['Upvotes'].max()}")
    print(f"Maior número de comentários: {df['Total Comentários'].max()}")