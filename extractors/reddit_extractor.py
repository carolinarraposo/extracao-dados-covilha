import os
import re
import json
import time
import praw
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
STATE_DIR = os.path.join(BASE_DIR, "data", "state")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)

LAST_RUN_FILE = os.path.join(STATE_DIR, "last_run_reddit.json")
JSON_FILE = os.path.join(RAW_DIR, "reddit_posts.json")
CLEAN_JSON_FILE = os.path.join(RAW_DIR, "reddit_posts_clean.json")


def criar_cliente_reddit():
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not client_id or not client_secret or not user_agent:
        print("Faltam credenciais do Reddit no .env")
        return None

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )


def carregar_ultimo_timestamp():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("ultimo_post")
    return None


def guardar_ultimo_timestamp(timestamp):
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
        json.dump({"ultimo_post": timestamp}, f, ensure_ascii=False, indent=4)


def clean_text(text):
    if text:
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"[^\w\s.,!?]", "", text)
    return text or ""


def extrair_post(post):
    post.comments.replace_more(limit=0)

    comments = []
    for comment in post.comments.list():
        comments.append({
            "comment_author": comment.author.name if comment.author else "Deleted",
            "comment_text": clean_text(comment.body),
            "comment_upvotes": comment.score
        })

    return {
        "source": "reddit",
        "platform_id": post.id,
        "title": post.title,
        "author": post.author.name if post.author else "Deleted",
        "text": clean_text(post.selftext),
        "created_at": datetime.fromtimestamp(post.created_utc, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "url": post.url,
        "metrics": {
            "upvotes": post.score,
            "comments": post.num_comments
        },
        "comments": comments,
        "timestamp": post.created_utc
    }


def extrair_posts_novos():
    reddit = criar_cliente_reddit()
    if not reddit:
        return []

    ultimo_timestamp = carregar_ultimo_timestamp()
    posts_novos = []
    novo_mais_recente = None

    subreddit = reddit.subreddit("covilha")
    geradores = [
        subreddit.hot(limit=500),
        subreddit.controversial(time_filter="month", limit=1000)
    ]

    for gerador in geradores:
        for post in gerador:
            if novo_mais_recente is None or post.created_utc > novo_mais_recente:
                novo_mais_recente = post.created_utc

            if ultimo_timestamp and post.created_utc <= ultimo_timestamp:
                continue

            try:
                posts_novos.append(extrair_post(post))
                print(f"Reddit extraído: {post.title[:60]}...")
            except Exception as e:
                print(f"Erro ao processar post {post.url}: {e}")

            time.sleep(0.5)

    if novo_mais_recente:
        guardar_ultimo_timestamp(novo_mais_recente)

    return posts_novos


def carregar_existentes():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_resultados(posts_novos):
    if not posts_novos:
        print("Reddit: nenhum post novo encontrado.")
        return

    for p in posts_novos:
        p.pop("timestamp", None)

    todos = posts_novos + carregar_existentes()

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=4)

    df = pd.DataFrame(todos)
    df = df.drop_duplicates(subset=["title", "author", "url"])

    df.to_json(CLEAN_JSON_FILE, orient="records", indent=4, force_ascii=False)

    print(f"Reddit: {len(posts_novos)} posts novos guardados.")
    print(f"Reddit: total acumulado sem duplicados: {len(df)}")


def run():
    posts = extrair_posts_novos()
    guardar_resultados(posts)


if __name__ == "__main__":
    run()
