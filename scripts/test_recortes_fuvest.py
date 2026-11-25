"""Regressões de apresentação sobre os PDFs oficiais conferidos pelo SHA-256."""
import gzip
import json
import re
import unittest

import fitz
from PIL import Image
from preparar_recortes_fuvest import ROOT, INDICE, regioes_edicao


class RecortesFuvestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.edicoes = json.loads(gzip.decompress((ROOT / "acervo/fuvest/questoes.json.gz").read_bytes()))["edicoes"]
        cls.indice = json.loads(gzip.decompress(INDICE.read_bytes()))

    def test_acervo_completo_sem_questoes_vizinhas_e_com_apoios(self):
        total, total_apoios, alternativas_textuais = 0, 0, 0
        for e in self.edicoes:
            with fitz.open(ROOT / f"tmp/pdfs/fuvest/{e['ano']}/prova.pdf") as doc:
                partes, apoios = regioes_edicao(doc, e)
                total_apoios += len(apoios)
                for q in e["questoes"]:
                    chave = f"{e['ano']}/{q['numero']}"
                    row = self.indice[chave]
                    # A construção verifica cada título contra todos os recortes.
                    self.assertTrue(partes[q["numero"]], chave)
                    self.assertTrue(all(r in partes[q["numero"]] for r in row["regioesFonte"]), chave)
                    self.assertEqual(1, len(row["recortes"]), chave)
                    self.assertEqual("questao", row["recortes"][0]["tipo"])
                    self.assertEqual(q["conteudo"]["urlProva"], row["urlProva"])
                    for a in apoios.values():
                        if q["numero"] in a["numeros"]:
                            self.assertTrue(a["regioes"], chave)
                            self.assertTrue(all(r in partes[q["numero"]] for r in a["regioes"]), chave)
                    # 2021 tem fonte sem Unicode. Três questões de 2018 usam
                    # alternativas desenhadas. Esses casos são conferidos visualmente.
                    if e["ano"] != 2021 and (e["ano"], q["numero"]) not in {(2018, 19), (2018, 21), (2018, 25)}:
                        texto = "\n".join(doc[r["pagina"] - 1].get_text(clip=fitz.Rect(r["caixa"]))
                                          for r in partes[q["numero"]] if r["tipo"] == "questao")
                        self.assertEqual(set("ABCDE"), set(re.findall(r"\(\s*([A-E])\s*\)", texto)), chave)
                        alternativas_textuais += 1
                    imagem = ROOT / "src/main/resources/static" / row["recortes"][0]["imagem"].lstrip("/")
                    with Image.open(imagem) as im:
                        self.assertEqual("WEBP", im.format)
                        self.assertGreater(im.width, 650)
                        self.assertGreater(im.height, 100)
                        im.verify()
                    total += 1
        self.assertEqual(890, total)
        self.assertEqual(69, total_apoios)
        self.assertEqual(797, alternativas_textuais)

    def test_paginas_largas_continuacoes_e_ordem_fisica(self):
        for chave in ("2018/57", "2021/18", "2021/43", "2025/1", "2026/52", "2027/21"):
            self.assertTrue(any(r["caixa"][2] - r["caixa"][0] > 500
                                for r in self.indice[chave]["regioesFonte"]), chave)
        self.assertEqual(2, sum(r["tipo"] == "apoio" for r in self.indice["2027/52"]["regioesFonte"]))
        # A faixa inferior contém enunciado e alternativas da questão 90,
        # abaixo das duas colunas das questões 88 e 89.
        q90 = [r for r in self.indice["2021/90"]["regioesFonte"] if r["tipo"] == "questao"]
        self.assertEqual(26, q90[0]["pagina"])
        self.assertGreater(q90[0]["caixa"][2] - q90[0]["caixa"][0], 500)
        self.assertTrue(all(r["caixa"][3] <= 571.21 for r in self.indice["2021/89"]["regioesFonte"]))


if __name__ == "__main__":
    unittest.main()
