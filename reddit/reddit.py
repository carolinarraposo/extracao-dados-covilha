import praw
import pandas as pd
import time
import json
from datetime import datetime, timezone
import re

reddit = praw.Reddit(
    client_id="gre8v6jDpK1512CIj09FWA",
    client_secret="ruvecE72wskQ8KAdThYxNEoEtKisCQ",
    user_agent="ETD/1.0"
)

posts_data = []
subreddit = reddit.subreddit("covilha")

def clean_text(text):
    if text:
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\w\s.,!?]', '', text)
    return text

for post in subreddit.hot(limit=500):
    # Carregar todos os comentários (pode ser demorado)
    post.comments.replace_more(limit=0) 
    
    comments_list = []
    for comment in post.comments.list():
        comments_list.append({
            "Autor": comment.author.name if comment.author else "Deleted",
            "Texto": clean_text(comment.body),
            "Upvotes": comment.score
        })

    posts_data.append({
        "Título": post.title,
        "Autor": post.author.name if post.author else "Deleted",
        "Texto": clean_text(post.selftext),
        "Upvotes": post.score,
        "Total Comentários": post.num_comments,
        "Conteudo_Comentarios": comments_list,
        "Data": datetime.fromtimestamp(post.created_utc, timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        "URL": post.url
    })
    time.sleep(0.5)

for post in subreddit.controversial(time_filter="month", limit=1000):
    posts_data.append({
        "Título": post.title,
        "Autor": post.author.name if post.author else "Deleted",
        "Texto": clean_text(post.selftext),
        "Upvotes": post.score,
        "Total Comentários": post.num_comments,
        "Conteudo_Comentarios": comments_list,
        "Data": datetime.fromtimestamp(post.created_utc, timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        "URL": post.url
    })
    time.sleep(0.5)

with open("reddit_posts.json", "w", encoding="utf-8") as f:
    json.dump(posts_data, f, ensure_ascii=False, indent=4)

df = pd.DataFrame(posts_data)

total_posts = len(df)
print(f"Total de posts recolhidos: {total_posts}")


json_file = "reddit_posts.json"

with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

num_duplicadas = df.duplicated(subset=["Título", "Autor", "URL"]).sum()
print(f"Total de posts duplicados encontrados: {num_duplicadas}")

df = df.drop_duplicates(subset=["Título", "Autor", "URL"])
print("Total de linhas duplicadas:" , df.duplicated(subset=["Título", "Autor", "URL"]).sum())

json_clean_file = "reddit_posts_clean.json"
df.to_json(json_clean_file, orient="records", indent=4, force_ascii=False)

print(f"Arquivo JSON limpo guardado em: {json_clean_file}")
total_posts = len(df)
print(f"Total de posts recolhidos: {total_posts}")

avg_upvotes = df['Upvotes'].mean()
avg_comments = df['Total Comentários'].mean()
max_upvotes = df['Upvotes'].max()
max_comments = df['Total Comentários'].max()

print("\nEstatísticas agregadas:")
print(f"Média de upvotes por post: {avg_upvotes:.2f}")
print(f"Média de comentários por post: {avg_comments:.2f}")
print(f"Maior número de upvotes em um post: {max_upvotes}")
print(f"Maior número de comentários em um post: {max_comments}")