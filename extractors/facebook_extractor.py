import os
import json
import csv
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
API_VERSION = "v25.0"

JSON_FILE = os.path.join(RAW_DIR, "facebook_posts.json")
CSV_FILE = os.path.join(RAW_DIR, "facebook_posts.csv")


def fetch_facebook_data():
    if not ACCESS_TOKEN:
        print("Falta FACEBOOK_ACCESS_TOKEN no .env")
        return []

    url = f"https://graph.facebook.com/{API_VERSION}/me/posts"
    params = {
        "fields": "id,message,created_time,comments{id,message,from,created_time}",
        "access_token": ACCESS_TOKEN,
        "limit": 100
    }

    posts_normalizados = []

    print("A extrair dados do Facebook...")

    while url:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()

        if "error" in data:
            print(f"Erro na API: {data['error']['message']}")
            break

        for post in data.get("data", []):
            comments = []
            for c in post.get("comments", {}).get("data", []):
                comments.append({
                    "comment_id": c.get("id"),
                    "author": c.get("from", {}).get("name") if c.get("from") else None,
                    "text": c.get("message"),
                    "created_at": c.get("created_time")
                })

            posts_normalizados.append({
                "source": "facebook",
                "platform_id": post.get("id"),
                "author": None,
                "text": post.get("message", ""),
                "created_at": post.get("created_time"),
                "metrics": {},
                "comments": comments
            })

        url = data.get("paging", {}).get("next")
        params = {}

    return posts_normalizados


def guardar_resultados(posts):
    if not posts:
        print("Facebook: nenhum dado guardado.")
        return

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["post_id", "post_date", "post_text", "comment_id", "comment_text"])

        for post in posts:
            comments = post.get("comments", [])
            if not comments:
                writer.writerow([
                    post.get("platform_id"),
                    post.get("created_at"),
                    post.get("text"),
                    "",
                    ""
                ])
            else:
                for c in comments:
                    writer.writerow([
                        post.get("platform_id"),
                        post.get("created_at"),
                        post.get("text"),
                        c.get("comment_id"),
                        c.get("text")
                    ])

    print(f"Facebook: {len(posts)} posts guardados.")


def run():
    posts = fetch_facebook_data()
    guardar_resultados(posts)


if __name__ == "__main__":
    run()
