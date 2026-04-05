import os
import requests
import csv
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
COMMENT_THREADS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
REPLIES_URL = "https://www.googleapis.com/youtube/v3/comments"

MAX_VIDEOS = 800
CHECKPOINT_INTERVAL = 5
QUERY = "covilhã"

VIDEOS_CSV = "youtube_videos.csv"
COMMENTS_CSV = "youtube_comments.csv"

colunas_comentarios = ["video_id", "comment_id", "parent_id", "author", "comment_text", "likes", "published_date"]
colunas_videos = ["video_id", "video_url", "title", "description", "channel", "published_date", "views", "likes", "comments_count"]

video_ids = []
videos_data = []
comments_data = []


def fazer_pedido(url, params, tentativas=5):
    for tentativa in range(tentativas):
        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 400:
                print("Erro 400 - detalhes:")
                print(response.json())
                return None

            if response.status_code == 403:
                print("Acesso negado")
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
            print(f"Erro de ligação (tentativa {tentativa + 1}): {e}")
            time.sleep(2)

    print("Falha definitiva no pedido")
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


def carregar_videos_existentes(nome_ficheiro):
    dados = []
    if os.path.exists(nome_ficheiro):
        with open(nome_ficheiro, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("video_id"):
                    dados.append(row)
    return dados


def carregar_comentarios_existentes(nome_ficheiro):
    dados = []
    if os.path.exists(nome_ficheiro):
        with open(nome_ficheiro, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("comment_id"):
                    dados.append(row)
    return dados


ids_videos_existentes = carregar_ids_existentes(VIDEOS_CSV, "video_id")
ids_comentarios_existentes = carregar_ids_existentes(COMMENTS_CSV, "comment_id")

print(f"Vídeos já existentes: {len(ids_videos_existentes)}")
print(f"Comentários já existentes: {len(ids_comentarios_existentes)}")

print("A pesquisar vídeos...")

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

    novos = 0
    for item in response["items"]:
        vid = item["id"]["videoId"]
        if vid not in ids_videos_existentes and vid not in video_ids:
            video_ids.append(vid)
            novos += 1

        if len(ids_videos_existentes) + len(video_ids) >= MAX_VIDEOS:
            break

    print(f"Vídeos novos recolhidos nesta página: {novos}")
    print(f"Total de vídeos novos nesta execução: {len(video_ids)}")

    if len(ids_videos_existentes) + len(video_ids) >= MAX_VIDEOS:
        break

    next_page = response.get("nextPageToken")
    if not next_page:
        break

    time.sleep(0.2)

print(f"Total de vídeos novos: {len(video_ids)}")

print("A extrair metadados...")

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

    print(f"Processados {min(i + 50, len(video_ids))}/{len(video_ids)} vídeos")

print(f"Metadados de {len(videos_data)} vídeos recolhidos")

print("A extrair comentários e respostas...")

for idx, vid in enumerate(video_ids):
    expected = comment_totals.get(vid, 0)
    print(f"Vídeo {idx + 1}/{len(video_ids)} -> {vid} (esperados: {expected} comentários)")

    if expected == 0:
        print("Sem comentários")
        continue

    next_page = None
    total_collected = 0

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
            print("Sem comentários ou erro")
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
                total_collected += 1

            if item["snippet"]["totalReplyCount"] > 0:
                reply_page = None

                while True:
                    reply_params = {
                        "part": "snippet",
                        "parentId": comment_id,
                        "maxResults": 100,
                        "textFormat": "plainText",
                        "key": API_KEY
                    }

                    if reply_page:
                        reply_params["pageToken"] = reply_page

                    reply_response = fazer_pedido(REPLIES_URL, reply_params)
                    if not reply_response or "items" not in reply_response:
                        break

                    for reply in reply_response["items"]:
                        r = reply["snippet"]
                        reply_id = reply["id"]

                        if reply_id not in ids_comentarios_existentes:
                            comments_data.append({
                                "video_id": vid,
                                "comment_id": reply_id,
                                "parent_id": comment_id,
                                "author": r["authorDisplayName"],
                                "comment_text": r["textDisplay"],
                                "likes": r["likeCount"],
                                "published_date": r["publishedAt"]
                            })
                            ids_comentarios_existentes.add(reply_id)
                            total_collected += 1

                    reply_page = reply_response.get("nextPageToken")
                    if not reply_page:
                        break

                    time.sleep(0.2)

        print(f"Recolhidos nesta execução para o vídeo: {total_collected}")

        next_page = response.get("nextPageToken")
        if not next_page:
            break

        time.sleep(0.2)

    if (idx + 1) % CHECKPOINT_INTERVAL == 0:
        print(f"Checkpoint aos {idx + 1} vídeos")

        if comments_data:
            guardar_csv(COMMENTS_CSV, comments_data, colunas_comentarios)
            comments_data.clear()

        if videos_data:
            guardar_csv(VIDEOS_CSV, videos_data, colunas_videos)
            videos_data.clear()

    time.sleep(1)

print("A guardar dados finais...")

if videos_data:
    guardar_csv(VIDEOS_CSV, videos_data, colunas_videos)

if comments_data:
    guardar_csv(COMMENTS_CSV, comments_data, colunas_comentarios)

print("Extração concluída")