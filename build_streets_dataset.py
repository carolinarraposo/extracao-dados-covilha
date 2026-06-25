"""
Gera o dataset de ruas oficiais do município da Covilhã com freguesias pós-2013.

Fontes necessárias (descarregar manualmente):
  todos_cp.txt               — CTT (ficheiro de todos os códigos postais de Portugal)
                               Disponível em: https://www.ctt.pt (requer registo)
  cod_post_freg_matched.csv  — dssg-pt/mp-mapeamento-cp7
                               https://github.com/dssg-pt/mp-mapeamento-cp7

Uso:
  python build_streets_dataset.py
  python build_streets_dataset.py --ctt caminho/todos_cp.txt --cp_freg caminho/matched.csv

O ficheiro resultante (streets_covilha.csv) deve ser copiado para
data/streets_covilha.csv no repositório agente-gestao-incidentes.
"""

import argparse
import os
import pandas as pd


# Códigos postais que não constavam no ficheiro de mapeamento dssg-pt.
# Freguesias verificadas manualmente no site dos CTT.
# Freguesias conhecidas sem cobertura CTT a nível de artéria.
# Ruas retiradas do dataset oficial do município (PDF).
MANUAL_STREET_ADDITIONS = [
    {"Nome da rua": "Rua Direita",              "Freguesia": "VERDELHOS"},
    {"Nome da rua": "Rua Direita da Burralheira","Freguesia": "VERDELHOS"},
    {"Nome da rua": "Travessa da Rua Direita",  "Freguesia": "VERDELHOS"},
]

MANUAL_CP_CORRECTIONS = {
    6200586: "ORJAIS",             # Orjais
    6225139: "CASEGAS E OURONDO",  # Casegas
    6225126: "CASEGAS E OURONDO",  # Casegas
    6215176: "CORTES DO MEIO",     # Cortes do Meio
    6215120: "CORTES DO MEIO",     # Cortes do Meio (CPALF confirma)
    6200357: "COVILHÃ E CANHOSO",  # São Martinho → Covilhã e Canhoso
    6215097: "BARCO E COUTADA",    # Barco → Barco e Coutada
}

COLS_CTT = [
    "DD", "CC", "LLLL", "LOCALIDADE",
    "ART_COD", "ART_TIPO", "PRI_PREP", "ART_TITULO", "SEG_PREP", "ART_DESIG",
    "ART_LOCAL", "TROCO", "PORTA", "CLIENTE",
    "CP4", "CP3", "CPALF",
]

DEFAULT_CTT = os.path.join(os.path.dirname(__file__), "data", "raw", "todos_cp.txt")
DEFAULT_CP_FREG = os.path.join(os.path.dirname(__file__), "data", "raw", "cod_post_freg_matched.csv")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(__file__), "data", "streets_covilha.csv")


def normalize_freguesia(name: str) -> str:
    """
    Converte para maiúsculas e remove o prefixo 'União das freguesias de'
    para ficar no mesmo formato do dataset original (ex: COVILHÃ E CANHOSO).
    """
    if not isinstance(name, str):
        return ""
    name = name.strip()
    for prefix in ("União das freguesias de ", "União das Freguesias de "):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    return name.upper()


def build_street_name(row) -> str:
    """Reconstrói o nome completo da rua a partir dos campos ART_* do ficheiro CTT."""
    parts = [row["ART_TIPO"], row["PRI_PREP"], row["ART_TITULO"], row["SEG_PREP"], row["ART_DESIG"]]
    tokens = [str(p).strip() for p in parts if pd.notna(p) and str(p).strip() not in ("", "nan")]
    return " ".join(tokens)


def main(ctt_path: str, cp_freg_path: str, output_path: str):
    print("A carregar cod_post_freg_matched.csv...")
    cp_freg = pd.read_csv(cp_freg_path, encoding="utf-8")
    covilha_cp = cp_freg[cp_freg["Concelho"] == "Covilhã"][
        ["CodigoPostal", "Freguesia Final (Pós RATF)"]
    ].copy()
    covilha_cp["Freguesia"] = covilha_cp["Freguesia Final (Pós RATF)"].apply(normalize_freguesia)
    # Substituir entradas NaN pelas correções manuais verificadas no site CTT
    correction_cps = set(MANUAL_CP_CORRECTIONS.keys())
    covilha_cp = covilha_cp[~covilha_cp["CodigoPostal"].isin(correction_cps)]
    corrections = pd.DataFrame([
        {"CodigoPostal": cp, "Freguesia": freg}
        for cp, freg in MANUAL_CP_CORRECTIONS.items()
    ])
    covilha_cp = pd.concat([covilha_cp, corrections], ignore_index=True)
    print(f"  {len(covilha_cp)} códigos postais de Covilhã encontrados (incl. correções manuais).")

    print("A carregar todos_cp.txt (pode demorar)...")
    ctt = pd.read_csv(
        ctt_path,
        sep=";",
        header=None,
        names=COLS_CTT,
        encoding="latin-1",
        dtype=str,
        low_memory=False,
    )

    ctt["CP4"] = ctt["CP4"].str.strip().str.zfill(4)
    ctt["CP3"] = ctt["CP3"].str.strip().str.zfill(3)
    ctt["CodigoPostal"] = (ctt["CP4"] + ctt["CP3"]).apply(
        lambda x: int(x) if str(x).isdigit() else None
    )
    ctt = ctt.dropna(subset=["CodigoPostal"])
    ctt["CodigoPostal"] = ctt["CodigoPostal"].astype(int)

    print("A filtrar entradas de Covilhã...")
    ctt_covilha = ctt.merge(covilha_cp, on="CodigoPostal", how="inner")
    print(f"  {len(ctt_covilha)} linhas CTT de Covilhã encontradas.")

    print("A reconstruir nomes de rua...")
    ctt_covilha["Nome da rua"] = ctt_covilha.apply(build_street_name, axis=1)
    ctt_covilha = ctt_covilha[ctt_covilha["Nome da rua"].str.strip() != ""]

    ctt_covilha = ctt_covilha[ctt_covilha["Freguesia"].notna()]
    print(f"  {len(ctt_covilha)} entradas com nome de rua e freguesia.")

    additions = pd.DataFrame(MANUAL_STREET_ADDITIONS)
    base = pd.concat([ctt_covilha[["Nome da rua", "Freguesia"]], additions], ignore_index=True)

    result = (
        base
        .drop_duplicates()
        .sort_values(["Freguesia", "Nome da rua"])
        .reset_index(drop=True)
    )

    print(f"\nResultado: {len(result)} ruas únicas em {result['Freguesia'].nunique()} freguesias.")
    print("\nFreguesias encontradas:")
    for f in sorted(result["Freguesia"].unique()):
        n = len(result[result["Freguesia"] == f])
        print(f"  {f}: {n} ruas")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
    print(f"\nDataset guardado em: {output_path}")
    print("Copia este ficheiro para data/streets_covilha.csv no repositório agente-gestao-incidentes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera dataset de ruas da Covilhã com freguesias pós-2013.")
    parser.add_argument("--ctt",     default=DEFAULT_CTT,     help="Caminho para todos_cp.txt (CTT)")
    parser.add_argument("--cp_freg", default=DEFAULT_CP_FREG, help="Caminho para cod_post_freg_matched.csv")
    parser.add_argument("--output",  default=DEFAULT_OUTPUT,  help="Ficheiro CSV de saída")
    args = parser.parse_args()
    main(args.ctt, args.cp_freg, args.output)
