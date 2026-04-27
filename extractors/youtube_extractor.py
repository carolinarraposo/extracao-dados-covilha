import os
import csv
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

API_KEY = os.getenv("YOUTUBE_API_KEY")

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
COMMENT_THREADS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
REPLIES_URL = "https://www.googleapis.com/youtube/v3/comments"

MAX_VIDEOS = 800
QUERY = "covilhã"

VIDEOS_CSV = os.path.join(RAW_DIR, "youtube_videos.csv")
COMMENTS_CSV = os.path.join(RAW_DIR, "youtube_comments.csv")
JSON_FILE = os.path.join(RAW_DIR, "youtube_posts.json")

COLUNAS_COMENTARIOS = ["video_id", "comment_id", "parent_id", "author", "comment_text", "likes", "published_date"]
COLUNAS_VIDEOS = ["video_id", "video_url", "title", "description", "channel", "published_date", "views", "likes", "comments_count"]


def fazer_pedido(url, params, tentativas=5):
    for tentativa in range(tentativas):
        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 400:
                print("Erro 400:", response.json())
                return None

            if response.status_code == 403:
                print("Acesso negado ou quota excedida.")
                return None

            if response.status_code == 429:
                print("Demasiados pedidos, a aguardar 60 segundos...")
                time.sleep(60)
                continue

            if response.status_code != 200:
                print(f"Erro HTTP {response.status_code}")
                time.sleep(2)
                continue

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Erro de ligação, tentativa {tentativa + 1}: {e}")
            time.sleep(2)

    return None


def guardar_csv(nome_ficheiro, dados, colunas):
    ficheiro_existe = os.path.exists(nome_ficheiro)
    with open(nome_ficheiro, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colunas)
        if not ficheiro_existe:
            writer.writeheader()
        writer.writerows(dados)


def carregar_ids_existentes(nome_ficheiro, coluna_id):
    ids = set()
    if os.path.exists(nome_ficheiro):
        with open(nome_ficheiro, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                valor = row.get(coluna_id)
                if valor:
                    ids.add(valor)
    return ids


def pesquisar_videos(ids_videos_existentes):
    video_ids = []

    params = {
        "part": "snippet",
        "q": QUERY,
        "type": "video",
        "maxResults": 50,
        "regionCode": "PT",
        "relevanceLanguage": "pt",
        "key": API_KEY
    }

    next_page = None

    while True:
        if next_page:
            params["pageToken"] = next_page
        elif "pageToken" in params:
            del params["pageToken"]

        response = fazer_pedido(SEARCH_URL, params)

        if not response or "items" not in response:
            break

        for item in response["items"]:
            vid = item["id"]["videoId"]

            if vid not in ids_videos_existentes and vid not in video_ids:
                video_ids.append(vid)

            if len(ids_videos_existentes) + len(video_ids) >= MAX_VIDEOS:
                break

        if len(ids_videos_existentes) + len(video_ids) >= MAX_VIDEOS:
            break

        next_page = response.get("nextPageToken")
        if not next_page:
            break

        time.sleep(0.2)

    return video_ids


def extrair_metadados(video_ids):
    videos_data = []
    comment_totals = {}

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]

        params = {
            "part": "snippet,statistics",
            "id": ",".join(batch),
            "key": API_KEY
        }

        response = fazer_pedido(VIDEOS_URL, params)
        if not response:
            continue

        for v in response.get("items", []):
            vid = v["id"]
            total_comments = int(v["statistics"].get("commentCount", 0))
            comment_totals[vid] = total_comments

            videos_data.append({
                "video_id": vid,
                "video_url": f"https://www.youtube.com/watch?v={vid}",
                "title": v["snippet"]["title"],
                "description": v["snippet"]["description"],
                "channel": v["snippet"]["channelTitle"],
                "published_date": v["snippet"]["publishedAt"],
                "views": v["statistics"].get("viewCount", 0),
                "likes": v["statistics"].get("likeCount", 0),
                "comments_count": total_comments
            })

    return videos_data, comment_totals


def extrair_comentarios(video_ids, comment_totals, ids_comentarios_existentes):
    comments_data = []

    for idx, vid in enumerate(video_ids):
        expected = comment_totals.get(vid, 0)
        print(f"YouTube vídeo {idx + 1}/{len(video_ids)}: {vid}")

        if expected == 0:
            continue

        next_page = None

        while True:
            params = {
                "part": "snippet",
                "videoId": vid,
                "maxResults": 100,
                "textFormat": "plainText",
                "key": API_KEY
            }

            if next_page:
                params["pageToken"] = next_page

            response = fazer_pedido(COMMENT_THREADS_URL, params)
            if not response or "items" not in response:
                break

            for item in response["items"]:
                top = item["snippet"]["topLevelComment"]
                snippet = top["snippet"]
                comment_id = top["id"]

                if comment_id not in ids_comentarios_existentes:
                    comments_data.append({
                        "video_id": vid,
                        "comment_id": comment_id,
                        "parent_id": None,
                        "author": snippet["authorDisplayName"],
                        "comment_text": snippet["textDisplay"],
                        "likes": snippet["likeCount"],
                        "published_date": snippet["publishedAt"]
                    })
                    ids_comentarios_existentes.add(comment_id)

                if item["snippet"]["totalReplyCount"] > 0:
                    comments_data.extend(
                        extrair_respostas(comment_id, vid, ids_comentarios_existentes)
                    )

            next_page = response.get("nextPageToken")
            if not next_page:
                break

            time.sleep(0.2)

        time.sleep(1)

    return comments_data


def extrair_respostas(comment_id, video_id, ids_comentarios_existentes):
    replies = []
    reply_page = None

    while True:
        params = {
            "part": "snippet",
            "parentId": comment_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "key": API_KEY
        }

        if reply_page:
            params["pageToken"] = reply_page

        response = fazer_pedido(REPLIES_URL, params)
        if not response or "items" not in response:
            break

        for reply in response["items"]:
            r = reply["snippet"]
            reply_id = reply["id"]

            if reply_id not in ids_comentarios_existentes:
                replies.append({
                    "video_id": video_id,
                    "comment_id": reply_id,
                    "parent_id": comment_id,
                    "author": r["authorDisplayName"],
                    "comment_text": r["textDisplay"],
                    "likes": r["likeCount"],
                    "published_date": r["publishedAt"]
                })
                ids_comentarios_existentes.add(reply_id)

        reply_page = response.get("nextPageToken")
        if not reply_page:
            break

        time.sleep(0.2)

    return replies


def guardar_json_youtube(videos_data, comments_data):
    comentarios_por_video = {}

    for c in comments_data:
        comentarios_por_video.setdefault(c["video_id"], []).append({
            "comment_id": c.get("comment_id"),
            "parent_id": c.get("parent_id"),
            "author": c.get("author"),
            "text": c.get("comment_text"),
            "likes": c.get("likes"),
            "created_at": c.get("published_date")
        })

    posts = []

    for v in videos_data:
        posts.append({
            "source": "youtube",
            "platform_id": v.get("video_id"),
            "url": v.get("video_url"),
            "title": v.get("title"),
            "author": v.get("channel"),
            "text": v.get("description"),
            "created_at": v.get("published_date"),
            "metrics": {
                "views": v.get("views"),
                "likes": v.get("likes"),
                "comments": v.get("comments_count")
            },
            "comments": comentarios_por_video.get(v.get("video_id"), [])
        })

    existentes = []
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            existentes = json.load(f)

    todos = posts + existentes

    vistos = set()
    unicos = []
    for item in todos:
        pid = item.get("platform_id")
        if pid and pid not in vistos:
            vistos.add(pid)
            unicos.append(item)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(unicos, f, ensure_ascii=False, indent=4)


def run():
    if not API_KEY:
        print("Falta YOUTUBE_API_KEY no .env")
        return

    ids_videos_existentes = carregar_ids_existentes(VIDEOS_CSV, "video_id")
    ids_comentarios_existentes = carregar_ids_existentes(COMMENTS_CSV, "comment_id")

    print(f"YouTube: vídeos existentes: {len(ids_videos_existentes)}")
    print(f"YouTube: comentários existentes: {len(ids_comentarios_existentes)}")

    video_ids = pesquisar_videos(ids_videos_existentes)
    print(f"YouTube: novos vídeos encontrados: {len(video_ids)}")

    if not video_ids:
        return

    videos_data, comment_totals = extrair_metadados(video_ids)
    comments_data = extrair_comentarios(video_ids, comment_totals, ids_comentarios_existentes)

    if videos_data:
        guardar_csv(VIDEOS_CSV, videos_data, COLUNAS_VIDEOS)

    if comments_data:
        guardar_csv(COMMENTS_CSV, comments_data, COLUNAS_COMENTARIOS)

    guardar_json_youtube(videos_data, comments_data)

    print("YouTube: extração concluída.")


if __name__ == "__main__":
    run()
