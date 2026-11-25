"""Integridade do acervo publicado: imagens, gabaritos, apoios e isolamento."""
import gzip, json, unittest, re, hashlib, zipfile, io
from pathlib import Path
from PIL import Image
import fitz
ROOT=Path(__file__).resolve().parents[1]
def asset(path):
    code=path.split('/')[2].removeprefix('pci-')
    with zipfile.ZipFile(ROOT/'acervo/concursos'/('recortes-'+code+'.zip')) as z:
        return z.read(path)

class RecortesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(gzip.decompress((ROOT/'acervo/concursos/questoes-recortadas.json.gz').read_bytes()))
        cls.layout=json.loads((ROOT/'acervo/concursos/layout-recortes.json').read_text())
        cls.keys=json.loads((ROOT/'acervo/concursos/gabaritos-recortes.json').read_text())
    def test_dez_provas_364_questoes_gabaritos_e_uma_anulada(self):
        self.assertEqual(len(self.data['provas']),10)
        self.assertEqual(sum(len(p['questoes']) for p in self.data['provas']),364)
        self.assertEqual([(p['slug'],q['numero']) for p in self.data['provas'] for q in p['questoes'] if q['anulada']],[('primavera-2009',18)])
        for p in self.data['provas']:
            self.assertEqual([q['numero'] for q in p['questoes']],list(range(1,p['total']+1)))
            for q in p['questoes']:
                self.assertEqual(q['gabarito'],self.keys[p['slug']][str(q['numero'])])
                self.assertIn(''.join(a['letra'] for a in q['alternativas']),['ABCD','ABCDE'])
                if not q['anulada']:self.assertIn(q['gabarito'],[a['letra'] for a in q['alternativas']])
    def test_imagens_existem_tem_proporcao_original_e_nao_exibem_outra_questao(self):
        for p in self.data['provas']:
            pdf=fitz.open(stream=asset('questoes/concursos/pci-'+p['slug']+'/prova.pdf'),filetype='pdf')
            self.assertTrue(len(pdf)>0)
            for q in p['questoes']:
                rec=q['conteudo']['recortes']
                self.assertTrue(any(r['tipo']=='questao' for r in rec))
                for r in rec:
                    self.assertRegex(r['imagem'],r'^/questoes/concursos/pci-[a-z0-9-]+/[a-z0-9-]+\.webp$')
                    img=Image.open(io.BytesIO(asset(r['imagem'].lstrip('/'))));img.load()
                    self.assertEqual(img.size,(r['largura'],r['altura']))
                    x,y,x2,y2=r['caixa'];self.assertLessEqual(abs(img.width-(x2-x)*2.5),2);self.assertLessEqual(abs(img.height-(y2-y)*2.5),2)
                labels=re.findall(r'(?m)^(?:QUEST[ÃA]O\s+|QUESTA0\s+)(\d+)\b',q['enunciado'])
                self.assertTrue(all(int(n)==q['numero'] for n in labels),(p['codigo'],q['numero'],labels))
    def test_todos_apoios_declarados_estao_vinculados(self):
        for p in self.data['provas']:
            for apoio in self.layout.get(p['slug'],{}).get('apoios',[]):
                for n in apoio['questoes']:
                    self.assertGreaterEqual(sum(r['tipo']=='apoio' for r in p['questoes'][n-1]['conteudo']['recortes']),len(apoio['regioes']))
    def test_fontes_e_gabaritos_arquivados_com_hash(self):
        audit=json.loads((ROOT/'acervo/concursos/validacao-recortes.json').read_text())['provas']
        with zipfile.ZipFile(ROOT/'acervo/concursos/fontes-recortes.zip') as z:
            for p,a in zip(self.data['provas'],audit):
                self.assertEqual(hashlib.sha256(z.read(p['slug']+'/gabarito.pdf')).hexdigest(),a['gabaritoSha256'])
                self.assertEqual(hashlib.sha256(asset('questoes/concursos/pci-'+p['slug']+'/prova.pdf')).hexdigest(),a['provaSha256'])
if __name__=='__main__':unittest.main()
