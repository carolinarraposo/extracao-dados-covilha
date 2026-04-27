import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

THREADS_USER_ID = os.getenv("THREADS_USER_ID")
ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(RAW_DIR, "threads_posts.json")


def fazer_pedido(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=15)

        if response.status_code != 200:
            print(f"Erro HTTP {response.status_code}: {response.text}")
            return None

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Erro no pedido: {e}")
        return None


def extrair_respostas(thread_id):
    respostas = []

    url = f"https://graph.threads.net/v1.0/{thread_id}/replies"
    params = {
        "fields": "id,text,username,timestamp,permalink,like_count",
        "access_token": ACCESS_TOKEN,
        "limit": 100
    }

    while url:
        data = fazer_pedido(url, params)

        if not data:
            break

        for r in data.get("data", []):
            respostas.append({
                "reply_id": r.get("id"),
                "author": r.get("username"),
                "text": r.get("text"),
                "created_at": r.get("timestamp"),
                "url": r.get("permalink"),
                "likes": r.get("like_count")
            })

        url = data.get("paging", {}).get("next")
        params = None
        time.sleep(0.2)

    return respostas


def run():
    if not THREADS_USER_ID or not ACCESS_TOKEN:
        print("Faltam THREADS_USER_ID ou THREADS_ACCESS_TOKEN no .env")
        return []

    print("A extrair dados do Threads...")

    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    params = {
        "fields": "id,text,username,permalink,timestamp,media_type,like_count,reply_count,repost_count,quote_count",
        "access_token": ACCESS_TOKEN,
        "limit": 100
    }

    posts = []

    while url:
        data = fazer_pedido(url, params)

        if not data:
            break

        for item in data.get("data", []):
            thread_id = item.get("id")

            posts.append({
                "source": "threads",
                "platform_id": thread_id,
                "author": item.get("username"),
                "url": item.get("permalink"),
                "text": item.get("text", ""),
                "created_at": item.get("timestamp"),
                "media_type": item.get("media_type"),
                "metrics": {
                    "likes": item.get("like_count"),
                    "replies": item.get("reply_count"),
                    "reposts": item.get("repost_count"),
                    "quotes": item.get("quote_count")
                },
                "replies": extrair_respostas(thread_id)
            })

            time.sleep(0.3)

        url = data.get("paging", {}).get("next")
        params = None

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

    print(f"Threads: {len(posts)} publicações guardadas.")
    return posts


if __name__ == "__main__":
    run()
