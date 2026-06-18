"""
Consulta o OpenStreetMap (Overpass API) para obter ruas de cada freguesia
do município da Covilhã e funde com o dataset CTT existente.

Uso:
  python fetch_osm_streets.py
  python fetch_osm_streets.py --input data/streets_covilha.csv --output data/streets_covilha.csv
"""

import argparse
import time
import unicodedata
import urllib.parse

import pandas as pd
import requests

# Mapeamento: nome OSM → nome pós-2013 do dataset
# Apenas nomes suficientemente únicos para não causar falsos positivos globais.
# Nomes ambíguos como "Santa Maria", "São Pedro", "Conceição", "Barco", "Peso"
# são omitidos porque existem em muitos outros municípios/países.
OSM_TO_DATASET = {
    # Sem alteração — nomes únicos
    "Aldeia de São Francisco de Assis": "ALDEIA DE SÃO FRANCISCO DE ASSIS",
    "Boidobra":                         "BOIDOBRA",
    "Cortes do Meio":                   "CORTES DO MEIO",
    "Dominguizo":                       "DOMINGUIZO",
    "Erada":                            "ERADA",
    "Ferro":                            "FERRO",
    "Orjais":                           "ORJAIS",
    "Peraboa":                          "PERABOA",
    "São Jorge da Beira":               "SÃO JORGE DA BEIRA",
    "Sobral de São Miguel":             "SOBRAL DE SÃO MIGUEL",
    "Tortosendo":                       "TORTOSENDO",
    "Unhais da Serra":                  "UNHAIS DA SERRA",
    "Verdelhos":                        "VERDELHOS",
    # Agregações com nomes suficientemente específicos
    "Coutada":                          "BARCO E COUTADA",
    "Cantar-Galo":                      "CANTAR-GALO E VILA DO CARVALHO",
    "Vila do Carvalho":                 "CANTAR-GALO E VILA DO CARVALHO",
    "Casegas":                          "CASEGAS E OURONDO",
    "Ourondo":                          "CASEGAS E OURONDO",
    "Canhoso":                          "COVILHÃ E CANHOSO",
    "Sarzedo":                          "TEIXOSO E SARZEDO",
    "Vales do Rio":                     "PESO E VALES DO RIO",
    "Aldeia do Souto":                  "VALE FORMOSO E ALDEIA DO SOUTO",
    # Nomes pós-2013 das uniões (mais específicos)
    "Barco e Coutada":                  "BARCO E COUTADA",
    "Cantar-Galo e Vila do Carvalho":   "CANTAR-GALO E VILA DO CARVALHO",
    "Casegas e Ourondo":                "CASEGAS E OURONDO",
    "Covilhã e Canhoso":               "COVILHÃ E CANHOSO",
    "Peso e Vales do Rio":              "PESO E VALES DO RIO",
    "Teixoso e Sarzedo":               "TEIXOSO E SARZEDO",
    "Vale Formoso e Aldeia do Souto":   "VALE FORMOSO E ALDEIA DO SOUTO",
    # Paul com constraint de município (nome único em Covilhã)
    "Paul":                             "PAUL",
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DELAY_SECONDS = 3


def normalize(name: str) -> str:
    nfd = unicodedata.normalize("NFD", name)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").lower().strip()


def fetch_osm_streets(osm_name: str) -> set[str]:
    # Limita a pesquisa ao município da Covilhã (admin_level=6 em Portugal)
    # para evitar falsos positivos com nomes comuns ("Santa Maria", "São Pedro", etc.)
    query = (
        f'[out:json][timeout:30];'
        f'area[name="Covilhã"][admin_level="6"]->.concelho;'
        f'area[name="{osm_name}"](area.concelho);'
        f'way[highway][name](area);'
        f'out tags;'
    )
    url = OVERPASS_URL + "?data=" + urllib.parse.quote(query)
    try:
        r = requests.get(url, timeout=35, headers={"User-Agent": "agente-gestao-incidentes/1.0"})
        if r.status_code != 200:
            print(f"    [{osm_name}] HTTP {r.status_code} — a saltar")
            return set()
        elements = r.json().get("elements", [])
        return {e["tags"]["name"] for e in elements if "tags" in e and "name" in e["tags"]}
    except Exception as e:
        print(f"    [{osm_name}] erro: {e}")
        return set()


def main(input_path: str, output_path: str):
    import os
    # Se já existe um ficheiro de saída fundido, usa-o como base (acumulativo)
    base_path = output_path if os.path.exists(output_path) else input_path
    print(f"A carregar base: {base_path}")
    ctt = pd.read_csv(base_path, sep=";", encoding="utf-8-sig")
    print(f"  {len(ctt)} ruas na base atual")

    osm_rows = []
    seen_parishes = set()

    for osm_name, dataset_parish in OSM_TO_DATASET.items():
        if dataset_parish in seen_parishes:
            # Já consultámos esta freguesia neste nome — combinar resultados
            pass
        print(f"A consultar OSM: {osm_name} → {dataset_parish}")
        streets = fetch_osm_streets(osm_name)
        print(f"  {len(streets)} ruas encontradas")
        for s in streets:
            osm_rows.append({"Nome da rua": s, "Freguesia": dataset_parish})
        seen_parishes.add(dataset_parish)
        time.sleep(DELAY_SECONDS)

    osm_df = pd.DataFrame(osm_rows)
    print(f"\nTotal entradas OSM: {len(osm_df)}")

    # Fusão: CTT + OSM, desduplicar por nome normalizado + freguesia
    combined = pd.concat([ctt, osm_df], ignore_index=True)
    combined["_norm"] = combined["Nome da rua"].apply(normalize)
    combined = (
        combined
        .sort_values("Nome da rua")           # CTT tem nomes mais limpos — preferir
        .drop_duplicates(subset=["_norm", "Freguesia"])
        .drop(columns=["_norm"])
        .sort_values(["Freguesia", "Nome da rua"])
        .reset_index(drop=True)
    )

    print(f"\nResultado final: {len(combined)} ruas únicas em {combined['Freguesia'].nunique()} freguesias")
    print("\nFreguesias:")
    for f in sorted(combined["Freguesia"].dropna().unique()):
        n = len(combined[combined["Freguesia"] == f])
        n_ctt = len(ctt[ctt["Freguesia"] == f]) if f in ctt["Freguesia"].values else 0
        print(f"  {f}: {n} ruas (era {n_ctt} no CTT)")

    combined.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
    print(f"\nGuardado em: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Funde ruas CTT com dados OSM para o município da Covilhã.")
    parser.add_argument("--input-ctt", default="data/streets_covilha_ctt.csv",
                        help="Dataset base CTT (não modificado pelo script)")
    parser.add_argument("--output",    default="data/streets_covilha.csv",
                        help="Ficheiro de saída (CTT + OSM fundidos)")
    args = parser.parse_args()
    main(args.input_ctt, args.output)
