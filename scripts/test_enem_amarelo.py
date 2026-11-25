import gzip,json,re,unittest,zipfile
from pathlib import Path
from preparar_enem_amarelo import ACERVO

class AcervoEnemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset=json.loads(gzip.decompress((ACERVO/'questoes-recortadas.json.gz').read_bytes()))
        cls.sources=json.loads((ACERVO/'fontes-amarelo.json').read_text())['provas']

    def test_cadernos_e_numero_de_questoes(self):
        data=self.dataset
        self.assertEqual(data['estado'],'PREVIA_NAO_APROVADA')
        self.assertEqual(len(data['provas']),20)
        self.assertEqual({(p['ano'],p['dia']) for p in data['provas']},{(y,d) for y in range(2017,2027) for d in (1,2)})
        qs=[q for p in data['provas'] for q in p['questoes']]
        self.assertEqual(len(qs),1850)
        self.assertEqual(sum(not q['anulada'] for q in qs),1839)
        self.assertEqual(sum(len(q['alternativas']) for q in qs),9250)

    def test_idiomas_nao_duplicam_questoes_comuns(self):
        for p in self.dataset['provas']:
            qs=p['questoes']
            self.assertEqual(len({q['numero'] for q in qs}),len(qs))
            self.assertEqual(len({q['chave'] for q in qs}),len(qs))
            self.assertEqual(len(qs),95 if p['dia']==1 else 90)
            if p['dia']==1:
                for idioma in ['INGLES','ESPANHOL']:
                    filtered=[q for q in qs if q['idioma'] in [None,idioma]]
                    self.assertEqual(sorted(q['numeroOriginal'] for q in filtered),list(range(1,91)))

    def test_recortes_e_gabaritos(self):
        for p in self.dataset['provas']:
            for q in p['questoes']:
                self.assertEqual(q['anulada'],q['gabarito'] is None)
                if not q['anulada']:self.assertIn(q['gabarito'],'ABCDE')
                self.assertEqual(''.join(a['letra'] for a in q['alternativas']),'ABCDE')
                rs=q['conteudo']['recortes']
                self.assertTrue(any(r['tipo']=='questao' for r in rs))
                for r in rs:self.assertRegex(r['imagem'],r'^/questoes/enem/enem-20\d\d-dia-[12]-amarelo/[a-z0-9-]+\.webp$')
                self.assertNotRegex(q['enunciado'],r'(?i)PROPOSTA DE REDA|INSTRUÇÕES PARA A REDA')

    def test_apoio_somente_quando_necessario(self):
        cases=set()
        for p in self.dataset['provas']:
            for q in p['questoes']:
                support=[r for r in q['conteudo']['recortes'] if r['tipo']=='apoio']
                if support:
                    cases.add((p['ano'],q['numeroOriginal']))
                    self.assertIsNone(q['idioma'])
                    self.assertTrue(all(r['necessario'] and r['justificativa'] for r in support))
        self.assertEqual(cases,{(2025,n) for n in range(6,11)}|{(2026,n) for n in range(46,51)})

    def test_pacotes_contem_somente_recursos_referenciados(self):
        from PIL import Image
        for p in self.dataset['provas']:
            package=ACERVO/f"recortes-{p['ano']}-dia-{p['dia']}.zip"
            needed={r['imagem'].lstrip('/') for q in p['questoes'] for r in q['conteudo']['recortes']}
            needed.add(f"questoes/enem/{p['slug']}/prova.pdf")
            with zipfile.ZipFile(package) as z:
                self.assertEqual(set(z.namelist()),needed)
                self.assertIsNone(z.testzip())
                for name in needed:
                    if name.endswith('.webp'):
                        with z.open(name) as f:
                            image=Image.open(f);self.assertGreater(image.width,50);self.assertGreater(image.height,30);image.verify()

if __name__=='__main__':unittest.main()
