import os
import csv
import json
import time
from atproto import Client
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
STATE_DIR = os.path.join(BASE_DIR, "data", "state")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)

IDS_FILE = os.path.join(STATE_DIR, "bluesky_ids_vistos.json")
JSON_FILE = os.path.join(RAW_DIR, "bluesky_posts.json")
CSV_FILE = os.path.join(RAW_DIR, "bluesky_posts.csv")


def carregar_ids_vistos():
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def guardar_ids_vistos(ids):
    with open(IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, ensure_ascii=False, indent=4)


def carregar_json_existente():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def extrair_dados_bluesky(query="covilhã", max_paginas=5):
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_APP_PASSWORD")

    if not handle or not password:
        print("Faltam BLUESKY_HANDLE ou BLUESKY_APP_PASSWORD no .env")
        return []

    client = Client()
    client.login(handle, password)

    todos_dados = []
    ids_vistos = carregar_ids_vistos()
    novos_ids = set()
    cursor = None

    print(f"Posts já recolhidos: {len(ids_vistos)}")
    print(f"A iniciar busca por: {query}")

    for i in range(max_paginas):
        params = {"q": query, "limit": 100}
        if cursor:
            params["cursor"] = cursor

        try:
            busca = client.app.bsky.feed.search_posts(params=params)
        except Exception as e:
            print(f"Erro ao pesquisar página {i + 1}: {type(e).__name__} - {e}")
            print("A parar extração do Bluesky e a guardar o que já foi recolhido.")
            break

        if not busca.posts:
            print("Sem mais posts disponíveis.")
            break

        novos_nesta_pagina = 0

        for post in busca.posts:
            if post.uri in ids_vistos:
                continue

            try:
                thread = client.app.bsky.feed.get_post_thread(params={"uri": post.uri})
                comentarios = []

                if hasattr(thread.thread, "replies") and thread.thread.replies:
                    for reply in thread.thread.replies:
                        if hasattr(reply, "post"):
                            comentarios.append({
                                "comment_author": reply.post.author.handle,
                                "comment_text": reply.post.record.text,
                                "comment_likes": reply.post.like_count
                            })

                post_data = {
                    "source": "bluesky",
                    "platform_id": post.uri,
                    "author": post.author.handle,
                    "text": post.record.text,
                    "created_at": post.record.created_at,
                    "metrics": {
                        "likes": post.like_count,
                        "replies": post.reply_count
                    },
                    "comments": comentarios
                }

                todos_dados.append(post_data)
                novos_ids.add(post.uri)
                novos_nesta_pagina += 1

            except Exception as e:
                print(f"Erro no post {post.uri}: {e}")

            time.sleep(0.1)

        print(f"Página {i + 1}: {novos_nesta_pagina} posts novos")

        if novos_nesta_pagina == 0:
            break

        cursor = busca.cursor
        if not cursor:
            break

        time.sleep(0.5)

    ids_vistos.update(novos_ids)
    guardar_ids_vistos(ids_vistos)

    return todos_dados


def guardar_resultados(novos_dados):
    if not novos_dados:
        print("Bluesky: nenhum dado novo.")
        return

    existentes = carregar_json_existente()
    todos = novos_dados + existentes

    vistos = set()
    unicos = []
    for item in todos:
        pid = item.get("platform_id")
        if pid and pid not in vistos:
            vistos.add(pid)
            unicos.append(item)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(unicos, f, ensure_ascii=False, indent=4)

    ficheiro_existe = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not ficheiro_existe:
            writer.writerow(["created_at", "author", "text", "likes", "replies", "comments"])

        for p in novos_dados:
            comentarios = " | ".join([
                f"[@{c['comment_author']}: {c['comment_text']} (Likes: {c['comment_likes']})]"
                for c in p.get("comments", [])
            ])
            writer.writerow([
                p.get("created_at"),
                p.get("author"),
                p.get("text"),
                p.get("metrics", {}).get("likes"),
                p.get("metrics", {}).get("replies"),
                comentarios
            ])

    print(f"Bluesky: {len(novos_dados)} novos posts guardados.")


def run():
    dados = extrair_dados_bluesky()
    guardar_resultados(dados)


if __name__ == "__main__":
    run()
