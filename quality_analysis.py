"""
quality_analysis.py
--------------------
Relatório de qualidade dos dados extraídos.
Analisa os ficheiros JSON em data/raw/ e reporta estatísticas,
campos em falta, duplicados e possíveis problemas.

Uso:
    python quality_analysis.py
"""

import json
import os
import re
from datetime import datetime
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"

FICHEIROS = {
    "news":    "news_posts.json",
    "reddit":  "reddit_posts_clean.json",
    "bluesky": "bluesky_posts.json",
    "youtube": "youtube_posts.json",
}

CAMPOS_OBRIGATORIOS = ["source", "text", "created_at"]
CAMPOS_ESPERADOS = ["source", "platform_id", "text", "created_at"]


def carregar_dados(nome_ficheiro: str) -> list:
    path = RAW_DIR / nome_ficheiro
    if not path.exists():
        return []
    with open(path, encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def validar_data(valor: str) -> bool:
    if not valor or not isinstance(valor, str):
        return False
    valor = valor.strip()
    padroes = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{4}-\d{2}-\d{2}T",
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}",
        r"[A-Z][a-z]{2}, \d{1,2} [A-Z][a-z]{2} \d{4}",
        r"\d{2}/\d{2}/\d{4}",
        r"\d{10,13}$",
    ]
    return any(re.match(p, valor) for p in padroes)


def analisar_fonte(nome: str, dados: list) -> dict:
    total = len(dados)
    if total == 0:
        return {"total": 0, "problemas": ["Ficheiro vazio ou não encontrado"]}

    sem_texto = 0
    texto_curto = 0
    sem_data = 0
    data_invalida = 0
    sem_source = 0
    sem_platform_id = 0
    duplicados_id = 0
    tamanhos_texto = []

    ids_vistos = set()

    for item in dados:
        if not isinstance(item, dict):
            continue

        text = (item.get("text") or "").strip()
        if not text:
            sem_texto += 1
        else:
            tamanhos_texto.append(len(text))
            if len(text) < 20:
                texto_curto += 1

        created_at = item.get("created_at")
        if not created_at:
            sem_data += 1
        elif not validar_data(str(created_at)):
            data_invalida += 1

        if not item.get("source"):
            sem_source += 1

        pid = item.get("platform_id")
        if not pid:
            sem_platform_id += 1
        elif pid in ids_vistos:
            duplicados_id += 1
        else:
            ids_vistos.add(pid)

    resultado = {
        "total": total,
        "sem_texto": sem_texto,
        "texto_curto_lt20": texto_curto,
        "sem_data": sem_data,
        "data_formato_invalido": data_invalida,
        "sem_source": sem_source,
        "sem_platform_id": sem_platform_id,
        "duplicados_platform_id": duplicados_id,
        "texto_min": min(tamanhos_texto) if tamanhos_texto else 0,
        "texto_max": max(tamanhos_texto) if tamanhos_texto else 0,
        "texto_medio": round(sum(tamanhos_texto) / len(tamanhos_texto)) if tamanhos_texto else 0,
        "registos_validos": total - sem_texto - sem_source,
    }

    return resultado


def imprimir_relatorio(resultados: dict):
    print("=" * 70)
    print("  RELATÓRIO DE QUALIDADE DOS DADOS EXTRAÍDOS")
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    total_geral = 0
    total_validos = 0
    total_problemas = 0

    for nome, stats in resultados.items():
        total = stats["total"]
        total_geral += total
        print(f"\n{'-' * 70}")
        print(f"  {nome.upper()} ({FICHEIROS[nome]})")
        print(f"{'-' * 70}")

        if total == 0:
            print("  Sem dados.")
            continue

        validos = stats["registos_validos"]
        total_validos += validos

        print(f"  Total de registos:         {total}")
        print(f"  Registos válidos:          {validos} ({validos/total*100:.1f}%)")
        print()

        problemas = []
        if stats["sem_texto"] > 0:
            problemas.append(f"  Sem texto:                 {stats['sem_texto']}")
        if stats["texto_curto_lt20"] > 0:
            problemas.append(f"  Texto < 20 caracteres:     {stats['texto_curto_lt20']}")
        if stats["sem_data"] > 0:
            problemas.append(f"  Sem data:                  {stats['sem_data']}")
        if stats["data_formato_invalido"] > 0:
            problemas.append(f"  Data formato inválido:     {stats['data_formato_invalido']}")
        if stats["sem_source"] > 0:
            problemas.append(f"  Sem campo 'source':        {stats['sem_source']}")
        if stats["sem_platform_id"] > 0:
            problemas.append(f"  Sem 'platform_id':         {stats['sem_platform_id']}")
        if stats["duplicados_platform_id"] > 0:
            problemas.append(f"  Duplicados (platform_id):  {stats['duplicados_platform_id']}")

        if problemas:
            print("  Problemas encontrados:")
            for p in problemas:
                print(p)
            total_problemas += sum([
                stats["sem_texto"],
                stats["sem_source"],
                stats["duplicados_platform_id"],
            ])
        else:
            print("  Sem problemas encontrados.")

        print()
        print(f"  Comprimento do texto:")
        print(f"    Mínimo:  {stats['texto_min']} caracteres")
        print(f"    Médio:   {stats['texto_medio']} caracteres")
        print(f"    Máximo:  {stats['texto_max']} caracteres")

    print(f"\n{'=' * 70}")
    print(f"  RESUMO GERAL")
    print(f"{'=' * 70}")
    print(f"  Total de registos:         {total_geral}")
    print(f"  Total válidos:             {total_validos} ({total_validos/total_geral*100:.1f}% )" if total_geral > 0 else "")
    print(f"  Registos com problemas:    {total_problemas}")
    print(f"  Fontes ativas:             {sum(1 for s in resultados.values() if s['total'] > 0)}/{len(resultados)}")

    fontes_inativas = [n for n, s in resultados.items() if s["total"] == 0]
    if fontes_inativas:
        print(f"  Fontes sem dados:          {', '.join(fontes_inativas)}")

    print(f"{'=' * 70}")


def main():
    resultados = {}
    for nome, ficheiro in FICHEIROS.items():
        dados = carregar_dados(ficheiro)
        resultados[nome] = analisar_fonte(nome, dados)

    imprimir_relatorio(resultados)


if __name__ == "__main__":
    main()
