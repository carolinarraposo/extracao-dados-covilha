import os
import csv
import json
import time
from atproto import Client
from dotenv import load_dotenv

load_dotenv()

client = Client()
client.login(
    os.getenv("BLUESKY_HANDLE"),
    os.getenv("BLUESKY_APP_PASSWORD")
)

FICHEIRO_IDS = "bluesky_ids_vistos.json"

def carregar_ids_vistos():
    """Carrega os IDs de posts já recolhidos em execuções anteriores."""
    if os.path.exists(FICHEIRO_IDS):
        with open(FICHEIRO_IDS, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def guardar_ids_vistos(ids):
    """Guarda os IDs recolhidos para não repetir na próxima execução."""
    with open(FICHEIRO_IDS, "w", encoding="utf-8") as f:
        json.dump(list(ids), f)

def extrair_dados_bluesky(query, max_paginas=20):
    todos_dados = []
    ids_vistos = carregar_ids_vistos()
    novos_ids = set()
    cursor = None

    print(f"Posts já recolhidos em execuções anteriores: {len(ids_vistos)}")
    print(f"A iniciar busca por: {query}")

    for i in range(max_paginas):
        params = {'q': query, 'limit': 100}  # 100 é o máximo permitido pela API
        if cursor:
            params['cursor'] = cursor

        busca = client.app.bsky.feed.search_posts(params=params)

        if not busca.posts:
            print("Sem mais posts disponíveis.")
            break

        novos_nesta_pagina = 0

        for post in busca.posts:
            # Salta posts já recolhidos
            if post.uri in ids_vistos:
                continue

            try:
                thread = client.app.bsky.feed.get_post_thread(params={'uri': post.uri})
                comentarios_detalhes = []

                if hasattr(thread.thread, 'replies') and thread.thread.replies:
                    for reply in thread.thread.replies:
                        if hasattr(reply, 'post'):
                            comentarios_detalhes.append({
                                'autor_comentario': reply.post.author.handle,
                                'texto_comentario': reply.post.record.text,
                                'likes_comentario': reply.post.like_count
                            })

                post_data = {
                    'post_id': post.uri,
                    'autor': post.author.handle,
                    'texto': post.record.text,
                    'data': post.record.created_at,
                    'qtd_likes': post.like_count,
                    'qtd_replies': post.reply_count,
                    'comentarios': comentarios_detalhes
                }

                todos_dados.append(post_data)
                novos_ids.add(post.uri)
                novos_nesta_pagina += 1
                print(f"  Extraído: @{post.author.handle}")

            except Exception as e:
                print(f"  Erro no post {post.uri}: {e}")

            time.sleep(0.1)

        print(f"Página {i+1}: {novos_nesta_pagina} posts novos recolhidos")

        # Se todos os posts desta página já foram vistos, não vale a pena continuar
        if novos_nesta_pagina == 0:
            print("Todos os posts desta página já foram recolhidos. A parar.")
            break

        cursor = busca.cursor
        if not cursor:
            print("Sem mais páginas disponíveis.")
            break

        time.sleep(0.5)  # pausa entre páginas

    # Guarda os novos IDs para a próxima execução
    ids_vistos.update(novos_ids)
    guardar_ids_vistos(ids_vistos)
    print(f"\nTotal de posts novos recolhidos: {len(todos_dados)}")

    return todos_dados

# Execução
query = "covilhã"
dados_finais = extrair_dados_bluesky(query, max_paginas=20)

# Guardar JSON
with open('bluesky_posts.json', 'w', encoding='utf-8') as f:
    json.dump(dados_finais, f, ensure_ascii=False, indent=4)

# Guardar CSV
with open('bluesky_posts.csv', 'a', newline='', encoding='utf-8') as f:  # 'a' para acrescentar
    writer = csv.writer(f)
    if not os.path.exists('bluesky_posts.csv') or os.path.getsize('bluesky_posts.csv') == 0:
        writer.writerow(['Data', 'Autor', 'Texto', 'Likes', 'Respostas', 'Conteúdo_Comentários'])

    for p in dados_finais:
        txt_comentarios = " | ".join([
            f"[@{c['autor_comentario']}: {c['texto_comentario']} (Likes: {c['likes_comentario']})]"
            for c in p['comentarios']
        ])
        writer.writerow([p['data'], p['autor'], p['texto'], p['qtd_likes'], p['qtd_replies'], txt_comentarios])

print("Extração finalizada!")