<img alt="UBI Logo" height="150" src="informatica-ubi.jpg" width="150"/>

# Extração de Dados — Covilhã

Repositório partilhado de extração automática de dados de notícias e redes sociais relacionados com o município da Covilhã. Os dados extraídos são utilizados por dois projetos distintos:

- **Agente de Gestão de Incidentes** — enriquece a priorização de incidentes com contexto local ([agente-gestao-incidentes](https://github.com/carolinarraposo/agente-gestao-incidentes))
- **Motor de Análise de Sentimentos** — processa os textos para classificação de sentimento e modelação de tópicos ([municipal-sentiment-topic-engine](https://github.com/patriciamarcos/municipal-sentiment-topic-engine))

## Fontes de dados

| Fonte | Estado | Ficheiro gerado |
|-------|--------|-----------------|
| Notícias (RSS) | Ativo | `data/raw/news_posts.csv` |
| Reddit | Ativo | `data/raw/reddit_posts.json` |
| Bluesky | Ativo | `data/raw/bluesky_posts.csv` |
| YouTube | Ativo | `data/raw/youtube_posts.json` |
| Facebook | Desativado | — |
| Instagram | Desativado | — |
| Threads | Desativado | — |

## Estrutura do projeto

```
extractors/
  news_extractor.py       # Notícias via RSS/feeds
  reddit_extractor.py     # Posts do Reddit
  bluesky_extractor.py    # Posts do Bluesky
  youtube_extractor.py    # Vídeos e comentários do YouTube
  facebook_extractor.py   # Posts do Facebook (desativado)
  instagram_extractor.py  # Posts do Instagram (desativado)
  threads_extractor.py    # Posts do Threads (desativado)

data/
  raw/                    # Ficheiros CSV/JSON gerados pelos scrapers
  state/                  # Estado interno (IDs já vistos, última execução)

run_extractors.py         # Script principal — corre todos os extractores
```

## Instalação

```bash
git clone https://github.com/carolinarraposo/extracao-dados-covilha.git
cd extracao-dados-covilha

python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux/Mac

pip install -r requirements.txt

cp .env.example .env
# Editar .env com as chaves necessárias
```

## Variáveis de ambiente

Copia o ficheiro de exemplo e preenche com as tuas chaves:

```bash
cp .env.example .env
```

```env
# Reddit
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=...

# Bluesky
BLUESKY_HANDLE=...
BLUESKY_APP_PASSWORD=...

# YouTube
YOUTUBE_API_KEY=...

# Facebook (desativado)
FACEBOOK_ACCESS_TOKEN=...

# Instagram (desativado)
INSTAGRAM_USER_ID=...
INSTAGRAM_ACCESS_TOKEN=...

# Threads (desativado)
THREADS_USER_ID=...
THREADS_ACCESS_TOKEN=...
```

## Utilização

```bash
python run_extractors.py
```

Os ficheiros são guardados em `data/raw/`. Os logs de execução ficam em `logs/execution.log`.

## Integração com outros projetos

Os dados em `data/raw/` podem ser consumidos diretamente por outros projetos. Cada projeto é responsável por importar e processar os dados conforme as suas necessidades.
