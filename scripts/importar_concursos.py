"""Importação transacional da carga 06; credenciais exclusivamente no ambiente."""
import argparse
import json
import os
from pathlib import Path
import re
import ssl
import sys


ROOT = Path(__file__).resolve().parents[1]
CARGA = ROOT / "database/06_importacao_10_concursos_ensino_medio.sql"
CAMPOS = ("nome", "descricao", "tipo", "codigo", "edicao", "ano", "etapa",
          "caderno", "orgao", "cargo", "banca", "url_prova", "url_gabarito",
          "status_importacao")
LOCK = "evolua_concursos_importacao"


class ImportacaoError(Exception):
    pass


def ler_carga(path=CARGA):
    # Somente o INSERT de dados é lido. START/COMMIT/SELECT do arquivo manual
    # não são executados: a transação fica sob controle deste programa.
    source = re.sub(r"(?m)^\s*--[^\n]*", "", Path(path).read_text(encoding="utf-8"))
    match = re.search(r"INSERT\s+IGNORE\s+INTO\s+prova\s*\(([^)]+)\)\s*VALUES\s*", source, re.I)
    if not match or tuple(s.strip() for s in match[1].split(",")) != CAMPOS:
        raise ImportacaoError("Campos da carga SQL divergentes do contrato.")
    values = source[match.end():]
    token = re.compile(r"\s*(?:('(?:''|[^'\\])*')|(-?\d+)|(NULL)|([(),;]))", re.I)
    tokens = []
    pos = 0
    while True:
        m = token.match(values, pos)
        if not m:
            raise ImportacaoError("Valor SQL não suportado; revise a carga.")
        pos = m.end()
        if m[4] == ";":
            break
        tokens.append(("value", m[1][1:-1].replace("''", "'")) if m[1] else
                      ("value", int(m[2])) if m[2] else
                      ("value", None) if m[3] else ("syntax", m[4]))
    rows = []
    i = 0
    while i < len(tokens):
        if tokens[i] != ("syntax", "("):
            raise ImportacaoError("Linha SQL inválida.")
        i += 1
        row = []
        for field in CAMPOS:
            if i >= len(tokens) or tokens[i][0] != "value":
                raise ImportacaoError("Linha SQL incompleta.")
            row.append(tokens[i][1])
            i += 1
            expected = ")" if field == CAMPOS[-1] else ","
            if i >= len(tokens) or tokens[i] != ("syntax", expected):
                raise ImportacaoError("Separador SQL inválido.")
            i += 1
        rows.append(dict(zip(CAMPOS, row)))
        if i < len(tokens):
            if tokens[i] != ("syntax", ",") or i + 1 == len(tokens):
                raise ImportacaoError("Separador de provas inválido.")
            i += 1
    if len(rows) != 10 or len({r["codigo"] for r in rows}) != 10:
        raise ImportacaoError("A carga deve conter exatamente dez códigos únicos.")
    for r in rows:
        if (r["tipo"] != "CONCURSO" or r["status_importacao"] != "RASCUNHO"
                or not isinstance(r["codigo"], str) or not r["codigo"]
                or not all(isinstance(r[k], str) and r[k].startswith("https://")
                           for k in ("url_prova", "url_gabarito"))):
            raise ImportacaoError("Metadados inválidos na carga.")
    return rows


def configuracao(env):
    required = ("DB_HOST", "DB_NAME", "DB_USUARIO", "DB_SENHA")
    missing = [k for k in required if not env.get(k)]
    if missing:
        raise ImportacaoError("Configure as variáveis: " + ", ".join(missing))
    try:
        port = int(env.get("DB_PORT") or "3306")
        if not 1 <= port <= 65535:
            raise ValueError()
    except ValueError:
        raise ImportacaoError("DB_PORT inválida.") from None
    mode = env.get("DB_SSL_MODE", "VERIFY_IDENTITY").upper()
    if mode == "DISABLED":
        if env["DB_HOST"] not in ("127.0.0.1", "localhost", "::1"):
            raise ImportacaoError("TLS só pode ser desativado para testes locais.")
        tls = None
    elif mode in ("REQUIRED", "VERIFY_IDENTITY"):
        tls = ssl.create_default_context(cafile=env.get("DB_SSL_CA") or None)
        if mode == "REQUIRED":
            tls.check_hostname = False
            tls.verify_mode = ssl.CERT_NONE
    else:
        raise ImportacaoError("DB_SSL_MODE inválido.")
    return dict(host=env["DB_HOST"], port=port, database=env["DB_NAME"],
                user=env["DB_USUARIO"], password=env["DB_SENHA"],
                charset="utf8mb4", autocommit=False, connect_timeout=15,
                read_timeout=30, write_timeout=30, ssl=tls)


def validar_schema(cur):
    cur.execute("SELECT ENGINE FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='prova'")
    table = cur.fetchone()
    if not table or table["ENGINE"].upper() != "INNODB":
        raise ImportacaoError("A tabela prova deve existir e usar InnoDB.")
    cur.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='prova'")
    if not set(CAMPOS + ("id_prova",)).issubset({r["COLUMN_NAME"] for r in cur.fetchall()}):
        raise ImportacaoError("Schema incompleto; aplique a migração 03 com o administrador.")
    cur.execute("SELECT INDEX_NAME FROM information_schema.STATISTICS "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='prova' AND NON_UNIQUE=0 "
                "GROUP BY INDEX_NAME HAVING COUNT(*)=1 AND MIN(COLUMN_NAME)='codigo' "
                "AND MAX(COALESCE(SUB_PART,0))=0")
    if not cur.fetchall():
        raise ImportacaoError("Falta uma chave única completa para prova.codigo.")


def importar(conn, rows, aplicar=False):
    codes = [r["codigo"] for r in rows]
    placeholders = ",".join(["%s"] * len(codes))
    select = ("SELECT id_prova,codigo,tipo,status_importacao,url_prova,url_gabarito "
              f"FROM prova WHERE codigo IN ({placeholders}) ORDER BY codigo FOR UPDATE")
    acquired = False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT GET_LOCK(%s,15) AS adquirido", (LOCK,))
            acquired = int(cur.fetchone()["adquirido"] or 0) == 1
            if not acquired:
                raise ImportacaoError("Outra importação está em andamento.")
            validar_schema(cur)
            cur.execute("SET SESSION sql_mode = CONCAT_WS(',', @@SESSION.sql_mode, 'STRICT_ALL_TABLES')")
            conn.begin()
            cur.execute(select, codes)
            before = {r["codigo"]: r for r in cur.fetchall()}
            if any(r["tipo"] != "CONCURSO" for r in before.values()):
                raise ImportacaoError("Código já usado por outra categoria; dados preservados.")
            new = 0
            for row in rows:
                if row["codigo"] in before:
                    continue
                # INSERT simples: erros de conteúdo não são ocultados por IGNORE.
                cur.execute(f"INSERT INTO prova ({','.join(CAMPOS)}) VALUES "
                            f"({','.join(['%s'] * len(CAMPOS))})",
                            tuple(row[k] for k in CAMPOS))
                new += 1
            cur.execute(select, codes)
            after = cur.fetchall()
            if (len(after) != 10 or {r["codigo"] for r in after} != set(codes)
                    or any(r["tipo"] != "CONCURSO" or not r["url_prova"]
                           or not r["url_gabarito"]
                           or r["status_importacao"] not in ("RASCUNHO", "VALIDADA")
                           for r in after)):
                raise ImportacaoError("Conferência final falhou; a carga será revertida.")
            summary = dict(status="OK", modo="APLICADO" if aplicar else "SIMULACAO",
                           provas=10, novas=new, existentes=len(before),
                           questoes_importadas=0)
            if aplicar:
                conn.commit()
            else:
                conn.rollback()
            return summary
    except Exception:
        conn.rollback()
        raise
    finally:
        if acquired:
            with conn.cursor() as cur:
                cur.execute("SELECT RELEASE_LOCK(%s)", (LOCK,))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="Confirmar a transação; sem esta opção, simula e reverte.")
    parser.add_argument("--validar-arquivo", action="store_true", help="Validar a carga sem conectar ao MySQL.")
    args = parser.parse_args()
    conn = None
    try:
        rows = ler_carga()
        if args.validar_arquivo:
            print(json.dumps(dict(status="OK", provas=len(rows), modo="ARQUIVO")))
            return 0
        config = configuracao(os.environ)
        import pymysql
        conn = pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)
        # PyMySQL não pode continuar sem TLS quando o servidor não o oferece.
        if config["ssl"] is not None and not getattr(conn, "_secure", False):
            raise ImportacaoError("O servidor não negociou TLS; importação cancelada.")
        print(json.dumps(importar(conn, rows, args.aplicar), ensure_ascii=False))
        return 0
    except ImportacaoError as exc:
        print(str(exc), file=sys.stderr)
    except ImportError:
        print("Instale scripts/requirements-concursos.txt.", file=sys.stderr)
    except Exception:
        # Exceções de drivers podem conter host, usuário ou SQL; não são exibidas.
        print("Importação interrompida. Confira conexão, permissões e schema do banco.", file=sys.stderr)
    finally:
        if conn is not None:
            conn.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
