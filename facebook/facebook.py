import requests
import json
import csv
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURAÇÕES ---
# Cole aqui o seu Token gerado no Graph API Explorer
ACCESS_TOKEN = os.getenv('FACEBOOK_TOKEN')
API_VERSION = 'v25.0'

def fetch_facebook_data():
    url = f"https://graph.facebook.com/{API_VERSION}/me/posts"
    params = {
        'fields': 'id,message,created_time,comments{message,from,created_time}',
        'access_token': ACCESS_TOKEN,
        'limit': 200  # Quantidade de posts por "página"
    }

    all_posts = []
    
    print("Iniciando extração...")

    while url:
        response = requests.get(url, params=params)
        data = response.json()

        if 'error' in data:
            print(f"Erro na API: {data['error']['message']}")
            break

        posts = data.get('data', [])
        all_posts.extend(posts)

        # Verifica se existe uma próxima página de posts
        url = data.get('paging', {}).get('next')
        # Após a primeira chamada, os parâmetros já vão na URL do 'next'
        params = {} 
        
        print(f"Extraídos {len(all_posts)} posts até agora...")

    return all_posts

def save_data(posts):
    # 1. SALVAR EM JSON (Mantém a estrutura hierárquica completa)
    with open('facebook_test.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)
    print("Arquivo JSON salvo com sucesso!")

    # 2. SALVAR EM CSV (Formato "achatado" para Excel)
    # Como CSV é uma tabela, vamos criar uma linha para cada comentário
    with open('facebook_test.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        # Cabeçalho
        writer.writerow(['Post_ID', 'Post_Data', 'Post_Mensagem', 'Comentario_ID', 'Comentario_Texto'])

        for post in posts:
            post_id = post.get('id')
            post_date = post.get('created_time')
            post_msg = post.get('message', '[Sem texto]')

            comments_data = post.get('comments', {}).get('data', [])
            
            if not comments_data:
                # Se não houver comentários, salva apenas o post
                writer.writerow([post_id, post_date, post_msg, '', ''])
            else:
                for comment in comments_data:
                    writer.writerow([
                        post_id, 
                        post_date, 
                        post_msg, 
                        comment.get('id'), 
                        comment.get('message')
                    ])
    print("Arquivo CSV salvo com sucesso!")

if __name__ == "__main__":
    dados = fetch_facebook_data()
    if dados:
        save_data(dados)