import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_VERSION = "v25.0"
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(RAW_DIR, "instagram_posts.json")


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


def extrair_comentarios(media_id):
    comentarios = []

    url = f"https://graph.facebook.com/{API_VERSION}/{media_id}/comments"
    params = {
        "fields": "id,text,username,timestamp,like_count",
        "access_token": ACCESS_TOKEN,
        "limit": 100
    }

    while url:
        data = fazer_pedido(url, params)

        if not data:
            break

        for c in data.get("data", []):
            comentarios.append({
                "comment_id": c.get("id"),
                "author": c.get("username"),
                "text": c.get("text"),
                "created_at": c.get("timestamp"),
                "likes": c.get("like_count")
            })

        url = data.get("paging", {}).get("next")
        params = None
        time.sleep(0.2)

    return comentarios


def run():
    if not INSTAGRAM_USER_ID or not ACCESS_TOKEN:
        print("Faltam INSTAGRAM_USER_ID ou INSTAGRAM_ACCESS_TOKEN no .env")
        return []

    print("A extrair dados do Instagram...")

    url = f"https://graph.facebook.com/{API_VERSION}/{INSTAGRAM_USER_ID}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
        "access_token": ACCESS_TOKEN,
        "limit": 100
    }

    posts = []

    while url:
        data = fazer_pedido(url, params)

        if not data:
            break

        for item in data.get("data", []):
            media_id = item.get("id")

            posts.append({
                "source": "instagram",
                "platform_id": media_id,
                "url": item.get("permalink"),
                "text": item.get("caption", ""),
                "created_at": item.get("timestamp"),
                "media_type": item.get("media_type"),
                "media_url": item.get("media_url"),
                "metrics": {
                    "likes": item.get("like_count"),
                    "comments": item.get("comments_count")
                },
                "comments": extrair_comentarios(media_id)
            })

            time.sleep(0.3)

        url = data.get("paging", {}).get("next")
        params = None

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

    print(f"Instagram: {len(posts)} publicações guardadas.")
    return posts


if __name__ == "__main__":
    run()
