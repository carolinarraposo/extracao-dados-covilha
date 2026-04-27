import logging
import os
import time
from datetime import datetime

from extractors.bluesky_extractor import run as run_bluesky
from extractors.facebook_extractor import run as run_facebook
from extractors.instagram_extractor import run as run_instagram
from extractors.threads_extractor import run as run_threads
from extractors.news_extractor import run as run_news
from extractors.reddit_extractor import run as run_reddit
from extractors.youtube_extractor import run as run_youtube


BASE_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "execution.log")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)


def executar_extractor(nome, funcao):
    logging.info("=" * 60)
    logging.info(f"INÍCIO: {nome}")

    inicio = time.time()

    try:
        resultado = funcao()
        duracao = time.time() - inicio

        logging.info(f"STATUS: {nome} concluído com sucesso")
        logging.info(f"TEMPO: {duracao:.2f} segundos")

        if isinstance(resultado, list):
            logging.info(f"REGISTOS DEVOLVIDOS: {len(resultado)}")

        return {
            "nome": nome,
            "status": "sucesso",
            "tempo": duracao,
            "erro": None
        }

    except Exception as e:
        duracao = time.time() - inicio

        logging.exception(f"STATUS: {nome} falhou")

        return {
            "nome": nome,
            "status": "erro",
            "tempo": duracao,
            "erro": f"{type(e).__name__}: {e}"
        }


def main():
    inicio_total = time.time()

    logging.info("=" * 60)
    logging.info("INÍCIO DA EXTRAÇÃO AUTOMÁTICA")
    logging.info(f"DATA/HORA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 60)

    extractors = [
        ("Bluesky", run_bluesky),
        ("News", run_news),
        ("Reddit", run_reddit),
        ("YouTube", run_youtube),
        #("Facebook", run_facebook),
        #("Instagram", run_instagram),
        #("Threads", run_threads),
    ]

    resultados = []

    for nome, funcao in extractors:
        resultados.append(executar_extractor(nome, funcao))

    tempo_total = time.time() - inicio_total

    logging.info("=" * 60)
    logging.info("RESUMO FINAL DA EXTRAÇÃO")
    logging.info("=" * 60)

    for r in resultados:
        estado = "OK" if r["status"] == "sucesso" else "ERRO"
        logging.info(f"{estado} | {r['nome']} | {r['tempo']:.2f}s")

        if r["erro"]:
            logging.error(f"{r['nome']} | {r['erro']}")

    logging.info("-" * 60)
    logging.info(f"TEMPO TOTAL: {tempo_total:.2f} segundos")
    logging.info("EXTRAÇÃO TERMINADA")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()