<img alt="UBI Logo" height="150" src="informatica-ubi.jpg" width="150"/>

# Extração de Dados — Covilhã

> Repositório partilhado de extração automática de dados de notícias e redes sociais relacionados com o município da Covilhã, desenvolvido no âmbito da unidade curricular de Projeto 2025/2026 da Licenciatura em Inteligência Artificial e Ciência de Dados da Universidade da Beira Interior.

---

Os dados extraídos são utilizados por dois projetos distintos:

- **Agente de Gestão de Incidentes** — enriquece a priorização de incidentes com contexto local ([agente-gestao-incidentes](https://github.com/carolinarraposo/agente-gestao-incidentes))
- **Motor de Análise de Sentimentos** — processa os textos para classificação de sentimento e modelação de tópicos ([municipal-sentiment-topic-engine](https://github.com/patriciamarcos/municipal-sentiment-topic-engine))

---

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

---

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

database/
  init_db.py              # Inicialização da base de dados
  import_data.py          # Importação dos dados extraídos para a BD
  tabelas.sql             # Definição das tabelas

data/
  raw/                    # Ficheiros CSV/JSON gerados pelos extractores
  state/                  # Estado interno (IDs já vistos, última execução)

run_extractors.py         # Script principal, corre todos os extractores
build_streets_dataset.py  # Gera o dataset de ruas a partir dos dados CTT e OSM
fetch_osm_streets.py      # Extrai ruas do município via OpenStreetMap (Overpass API)
quality_analysis.py       # Relatório de qualidade dos dados extraídos
```

---

## Pré-requisitos

- Python 3.9+
- Conta Reddit com app criada em [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) (para extração do Reddit)
- Conta Bluesky com App Password gerada nas definições (para extração do Bluesky)
- Chave da YouTube Data API v3 via [Google Cloud Console](https://console.cloud.google.com/) (para extração do YouTube)

---

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

---

## Variáveis de ambiente

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

---

## Utilização

```bash
python run_extractors.py
```

Os ficheiros são guardados em `data/raw/`. Os logs de execução ficam em `logs/execution.log`.

---

## Dataset de ruas

O ficheiro `streets_covilha.csv` é gerado a partir de dados dos CTT e do OpenStreetMap:

```bash
python build_streets_dataset.py
```

O ficheiro resultante deve ser copiado para `data/streets_covilha.csv` no repositório `agente-gestao-incidentes`.

---
## Tecnologias

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![praw](https://img.shields.io/badge/praw-FF4500?style=flat&logo=reddit&logoColor=white)
![atproto](https://img.shields.io/badge/atproto-0085FF?style=flat&logo=bluesky&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?style=flat&logo=pandas&logoColor=white)

---
## Autoras

**Carolina Raposo** — Licenciatura em Inteligência Artificial e Ciência de Dados

**Patrícia Marcos** — Licenciatura em Inteligência Artificial e Ciência de Dados




