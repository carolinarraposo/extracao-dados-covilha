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


def extrair_dados_bluesky(query, max_paginas=5):
    todos_dados = []
    cursor = None

    print(f"Iniciando busca por: {query}")

    for i in range(max_paginas):
        params = {'q': query, 'limit': 25}  # Limite menor para evitar timeouts
        if cursor:
            params['cursor'] = cursor

        # Busca os posts
        busca = client.app.bsky.feed.search_posts(params=params)

        for post in busca.posts:
            # Obter a thread detalhada para ler os comentários (replies)
            try:
                thread = client.app.bsky.feed.get_post_thread(params={'uri': post.uri})
                comentarios_detalhes = []

                # Verificar se existem respostas na thread
                if hasattr(thread.thread, 'replies') and thread.thread.replies:
                    for reply in thread.thread.replies:
                        if hasattr(reply, 'post'):
                            comentarios_detalhes.append({
                                'autor_comentario': reply.post.author.handle,
                                'texto_comentario': reply.post.record.text,
                                'likes_comentario': reply.post.like_count
                            })

                # Estrutura do Post Principal
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
                print(f"Extraído post de @{post.author.handle}")

            except Exception as e:
                print(f"Erro ao processar post {post.uri}: {e}")

            # Pequena pausa para respeitar o rate limit
            time.sleep(0.1)

        cursor = busca.cursor
        if not cursor:
            break
        print(f"Página {i + 1} concluída...")

    return todos_dados


# 2. Execução
query = "covilhã"
dados_finais = extrair_dados_bluesky(query, max_paginas=2)

# 3. Guardar em JSON (Melhor para dados hierárquicos como comentários)
with open('bluesky_posts.json', 'w', encoding='utf-8') as f:
    json.dump(dados_finais, f, ensure_ascii=False, indent=4)

# 4. Guardar em CSV
# Nota: Como o CSV é plano, os comentários ficarão numa string formatada
with open('bluesky_posts.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Data', 'Autor', 'Texto', 'Likes', 'Respostas', 'Conteúdo_Comentários'])

    for p in dados_finais:
        # Formata comentários para caber numa célula do CSV
        txt_comentarios = " | ".join(
            [f"[@{c['autor_comentario']}: {c['texto_comentario']} (Likes: {c['likes_comentario']})]" for c in
             p['comentarios']])

        writer.writerow([
            p['data'],
            p['autor'],
            p['texto'],
            p['qtd_likes'],
            p['qtd_replies'],
            txt_comentarios
        ])

print("Extração finalizada! Ficheiros 'bluesky_posts.json' e 'bluesky_posts.csv' criados.")