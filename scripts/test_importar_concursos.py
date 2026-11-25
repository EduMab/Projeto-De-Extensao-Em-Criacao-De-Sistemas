import copy
import os
from pathlib import Path
import tempfile
import unittest

from importar_concursos import (CARGA, CAMPOS, ImportacaoError, ROOT,
                               configuracao, importar, ler_carga)


class CargaTest(unittest.TestCase):
    def test_carga_tem_dez_codigos_e_cadernos_em_rascunho(self):
        rows = ler_carga()
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({r["codigo"] for r in rows}), 10)
        self.assertEqual({r["status_importacao"] for r in rows}, {"RASCUNHO"})

    def test_rejeita_codigo_duplicado(self):
        source = CARGA.read_text().replace("TJSP-2023-ESCREVENTE-TECNICO", "INSS-2022-TECNICO-SEGURO-SOCIAL")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "carga.sql"
            path.write_text(source)
            with self.assertRaises(ImportacaoError):
                ler_carga(path)

    def test_rejeita_publicacao_automatica(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "carga.sql"
            path.write_text(CARGA.read_text().replace("'RASCUNHO'", "'VALIDADA'", 1))
            with self.assertRaises(ImportacaoError):
                ler_carga(path)

    def test_falta_credencial_nao_expoe_valores(self):
        with self.assertRaises(ImportacaoError) as ctx:
            configuracao({"DB_SENHA": "senha-que-nao-deve-aparecer"})
        self.assertIn("DB_HOST", str(ctx.exception))
        self.assertNotIn("senha-que-nao-deve-aparecer", str(ctx.exception))

    def test_nao_desliga_tls_remoto(self):
        with self.assertRaises(ImportacaoError):
            configuracao(dict(DB_HOST="mysql.example.com", DB_NAME="evoluamais",
                              DB_USUARIO="editor", DB_SENHA="teste", DB_SSL_MODE="DISABLED"))


@unittest.skipUnless(os.environ.get("RUN_MYSQL_TESTS") == "1", "Requer MySQL isolado")
class MySQLTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pymysql
        config = configuracao(os.environ)
        if config["database"] != "evolua_concursos_test":
            raise RuntimeError("Testes permitidos somente no banco evolua_concursos_test.")
        cls.conn = pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)
        schema = (ROOT / "database/01_estrutura.sql").read_text()
        import re
        schema = re.sub(r"(?m)^\s*--[^\n]*", "", schema)
        with cls.conn.cursor() as cur:
            for statement in schema.split(";"):
                if statement.strip():
                    cur.execute(statement)
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        self.rows = ler_carga()
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM prova")
        self.conn.commit()

    def records(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM prova ORDER BY codigo")
            return list(cur.fetchall())

    def seed(self, **changes):
        row = dict(self.rows[0], **changes)
        with self.conn.cursor() as cur:
            cur.execute(f"INSERT INTO prova ({','.join(CAMPOS)}) VALUES "
                        f"({','.join(['%s'] * len(CAMPOS))})", tuple(row[k] for k in CAMPOS))
        self.conn.commit()

    def test_importa_dez_e_reexecuta_sem_duplicatas(self):
        first = importar(self.conn, self.rows, aplicar=True)
        self.assertEqual(first["novas"], 10)
        original = self.records()
        second = importar(self.conn, self.rows, aplicar=True)
        self.assertEqual(second["novas"], 0)
        self.assertEqual(second["existentes"], 10)
        self.assertEqual(original, self.records())
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM questao")
            self.assertEqual(cur.fetchone()["total"], 0)

    def test_simulacao_reverte_todos_os_registros(self):
        result = importar(self.conn, self.rows)
        self.assertEqual(result["modo"], "SIMULACAO")
        self.assertEqual(result["novas"], 10)
        self.assertEqual(self.records(), [])

    def test_preserva_edicoes_ja_corrigidas(self):
        self.seed(nome="Nome revisado pelo grupo", status_importacao="VALIDADA")
        existing = self.records()[0]
        importar(self.conn, self.rows, aplicar=True)
        actual = {r["codigo"]: r for r in self.records()}
        self.assertEqual(actual[existing["codigo"]], existing)

    def test_conflito_com_outra_categoria_nao_importa(self):
        self.seed(tipo="ENEM")
        before = self.records()
        with self.assertRaises(ImportacaoError):
            importar(self.conn, self.rows, aplicar=True)
        self.assertEqual(self.records(), before)

    def test_falha_final_reverte_as_outras_nove(self):
        self.seed(url_gabarito=None)
        before = self.records()
        with self.assertRaises(ImportacaoError):
            importar(self.conn, self.rows, aplicar=True)
        self.assertEqual(self.records(), before)

    def test_erro_durante_insert_nao_deixa_importacao_parcial(self):
        bad = copy.deepcopy(self.rows)
        bad[-1]["ano"] = "ano-invalido"
        with self.assertRaises(Exception):
            importar(self.conn, bad, aplicar=True)
        self.assertEqual(self.records(), [])


if __name__ == "__main__":
    unittest.main()
