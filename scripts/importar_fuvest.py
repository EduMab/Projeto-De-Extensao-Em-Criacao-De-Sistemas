#!/usr/bin/env python3
"""Confere a carga FUVEST e importa uma edição por transação no MySQL."""
import argparse
import gzip
import json
import os
from pathlib import Path
import re

from importar_concursos import configuracao, ImportacaoError, validar_schema

ROOT = Path(__file__).resolve().parents[1]
ACERVO = ROOT / "acervo/fuvest"
STATIC = ROOT / "src/main/resources/static"
LOCK = "evolua_fuvest_importacao"
LETRAS = "ABCDE"


def validar_acervo():
    fontes = json.loads((ACERVO / "fontes.json").read_text(encoding="utf-8"))
    with gzip.open(ACERVO / "questoes.json.gz", "rt", encoding="utf-8") as arquivo:
        acervo = json.load(arquivo)
    edicoes = acervo["edicoes"]
    if (acervo["tipo"], acervo["formato"]) != ("FUVEST", 1) or len(edicoes) != 10:
        raise ImportacaoError("A carga FUVEST deve conter dez edições.")
    if [edicao["ano"] for edicao in edicoes] != list(range(2018, 2028)):
        raise ImportacaoError("Edições fora do recorte FUVEST 2018 a 2027.")
    for fonte, edicao in zip(fontes, edicoes, strict=True):
        ano = edicao["ano"]
        codigo = f"FUVEST-{ano}-FASE1-{fonte['caderno']}"
        if any(edicao[campo] != valor for campo, valor in fonte.items()) or edicao["codigo"] != codigo:
            raise ImportacaoError(f"Metadados divergentes da fonte: {ano}.")
        questoes = edicao["questoes"]
        if [q["numero"] for q in questoes] != list(range(1, edicao["total"] + 1)):
            raise ImportacaoError(f"Numeração incompleta em {ano}.")
        prefixo = f"/questoes/fuvest/{ano}-{edicao['sha256Prova'][:12]}/"
        for q in questoes:
            chave = q["gabarito"]
            c = q["conteudo"]
            if (not isinstance(chave, list) or len(chave) > 2
                    or any(a not in tuple(LETRAS) for a in chave) or len(set(chave)) != len(chave)
                    or q["anulada"] != (not chave) or c["modo"] != "pagina_original"
                    or c["numeroOriginal"] != q["numero"]
                    or c["urlProva"] != f"{fonte['prova']}#page={c['pagina']}"
                    or not re.fullmatch(r"[0-9a-f]{64}", q["hashFonte"])):
                raise ImportacaoError(f"Questão ou gabarito inválido: {codigo}/{q['numero']}.")
            if not any(p["numero"] == c["pagina"] and p["imagem"] == q["imagem"] for p in c["paginas"]):
                raise ImportacaoError(f"Página principal ausente: {codigo}/{q['numero']}.")
            for p in c["paginas"] + c["apoioAnterior"]:
                if (p["imagem"] != f"{prefixo}pagina-{p['numero']:02}.webp"
                        or not (STATIC / p["imagem"].lstrip("/")).is_file()):
                    raise ImportacaoError(f"Imagem ausente ou inválida: {p['imagem']}.")
    return edicoes


def importar_edicao(cur, edicao):
    ano = edicao["ano"]
    codigo = edicao["codigo"]
    metadados = ("FUVEST", str(ano), ano, "1ª fase", edicao["caderno"], edicao["prova"], edicao["gabarito"])
    cur.execute(
        """SELECT id_prova,tipo,edicao,ano,etapa,caderno,url_prova,url_gabarito
           FROM prova WHERE codigo=%s FOR UPDATE""", (codigo,))
    prova = cur.fetchone()
    if prova:
        campos = ("tipo", "edicao", "ano", "etapa", "caderno", "url_prova", "url_gabarito")
        if tuple(prova[campo] for campo in campos) != metadados:
            raise ImportacaoError(f"Prova existente diverge do catálogo: {codigo}.")
        id_prova = prova["id_prova"]
    else:
        cur.execute(
            """INSERT INTO prova(nome,descricao,codigo,tipo,edicao,ano,etapa,caderno,
                   url_prova,url_gabarito,banca,status_importacao)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'FUVEST','RASCUNHO')""",
            (f"FUVEST {ano} · 1ª fase · {edicao['caderno']}", "Caderno oficial de conhecimentos gerais.",
             codigo, *metadados))
        id_prova = cur.lastrowid

    cur.execute("SELECT id_disciplina FROM disciplina WHERE nome=%s ORDER BY id_disciplina LIMIT 1",
                ("Conhecimentos gerais",))
    disciplina = cur.fetchone()
    if disciplina:
        id_disciplina = disciplina["id_disciplina"]
    else:
        cur.execute("INSERT INTO disciplina(nome) VALUES (%s)", ("Conhecimentos gerais",))
        id_disciplina = cur.lastrowid

    cur.execute(
        """SELECT id_questao,numero_original,enunciado,imagem_url,anulada,conteudo_json,hash_fonte
           FROM questao WHERE id_prova=%s FOR UPDATE""", (id_prova,))
    existentes = {q["numero_original"]: q for q in cur.fetchall()}
    if set(existentes) - set(range(1, edicao["total"] + 1)):
        raise ImportacaoError(f"Numeração existente fora do caderno oficial: {codigo}.")

    for q in edicao["questoes"]:
        numero = q["numero"]
        anterior = existentes.get(numero)
        if anterior:
            if (anterior["hash_fonte"] != q["hashFonte"] or bool(anterior["anulada"]) != q["anulada"]
                    or anterior["enunciado"] != q["enunciado"] or anterior["imagem_url"] != q["imagem"]
                    or json.loads(anterior["conteudo_json"] or "null") != q["conteudo"]):
                raise ImportacaoError(f"Questão existente diverge do catálogo: {codigo}/{numero}.")
            cur.execute("SELECT letra,correta FROM alternativa WHERE id_questao=%s ORDER BY letra",
                        (anterior["id_questao"],))
            alternativas = cur.fetchall()
            if [(a["letra"], bool(a["correta"])) for a in alternativas] != [
                    (letra, letra in q["gabarito"]) for letra in LETRAS]:
                raise ImportacaoError(f"Gabarito existente diverge do oficial: {codigo}/{numero}.")
            continue

        cur.execute(
            """INSERT INTO questao(enunciado,id_disciplina,id_prova,numero_original,imagem_url,
                   anulada,conteudo_json,hash_fonte)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (q["enunciado"], id_disciplina, id_prova, numero, q["imagem"], int(q["anulada"]),
             json.dumps(q["conteudo"], ensure_ascii=False), q["hashFonte"]))
        id_questao = cur.lastrowid
        cur.executemany("INSERT INTO alternativa(texto,correta,id_questao,letra) VALUES (%s,%s,%s,%s)",
                        [(f"Alternativa {letra} do caderno original.", int(letra in q["gabarito"]),
                          id_questao, letra) for letra in LETRAS])

    cur.execute("SELECT COUNT(*) AS total FROM questao WHERE id_prova=%s", (id_prova,))
    if cur.fetchone()["total"] != edicao["total"]:
        raise ImportacaoError(f"Quantidade divergente após a carga: {codigo}.")
    cur.execute("UPDATE prova SET status_importacao='VALIDADA' WHERE id_prova=%s", (id_prova,))
    return edicao["total"] - len(existentes)


def importar(conn, edicoes, aplicar):
    with conn.cursor() as cur:
        cur.execute("SELECT GET_LOCK(%s, 15) AS adquirido", (LOCK,))
        if cur.fetchone()["adquirido"] != 1:
            raise ImportacaoError("Outra importação da FUVEST está em andamento.")
        try:
            validar_schema(cur)
            for edicao in edicoes:
                conn.begin()
                try:
                    novas = importar_edicao(cur, edicao)
                    if aplicar:
                        conn.commit()
                    else:
                        conn.rollback()
                except Exception:
                    conn.rollback()
                    raise
                modo = "Importada" if aplicar else "Simulada"
                print(f"{modo} {edicao['codigo']}: {novas} novas de {edicao['total']} questões.", flush=True)
        finally:
            cur.execute("SELECT RELEASE_LOCK(%s)", (LOCK,))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--simular", action="store_true", help="Executa no MySQL e reverte cada transação.")
    modo.add_argument("--aplicar", action="store_true", help="Confirma a carga no MySQL.")
    args = parser.parse_args()
    try:
        edicoes = validar_acervo()
        questoes = [q for edicao in edicoes for q in edicao["questoes"]]
        aptas = sum(len(q["gabarito"]) == 1 for q in questoes)
        print(f"Acervo conferido: {len(edicoes)} edições, {len(questoes)} questões, {aptas} aptas ao sorteio.",
              flush=True)
        if args.simular or args.aplicar:
            import pymysql
            with pymysql.connect(**configuracao(os.environ), cursorclass=pymysql.cursors.DictCursor) as conn:
                importar(conn, edicoes, args.aplicar)
    except (ImportacaoError, ValueError, OSError) as erro:
        parser.exit(1, f"Importação interrompida: {erro}\n")


if __name__ == "__main__":
    main()
