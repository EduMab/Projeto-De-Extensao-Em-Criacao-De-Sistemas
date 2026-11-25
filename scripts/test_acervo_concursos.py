import json, gzip
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class AcervoConcursosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provas=json.loads(gzip.decompress((ROOT/'acervo/concursos/questoes.json.gz').read_bytes()))['provas']
    def test_acervo_completo(self):
        self.assertEqual(len(self.provas),10)
        self.assertEqual(sum(len(e['questoes']) for e in self.provas),830)
        self.assertEqual(sum(q['anulada'] for e in self.provas for q in e['questoes']),30)
        self.assertEqual(sum(len(q['alternativas']) for e in self.provas for q in e['questoes']),2990)
    def test_numeracao_e_gabaritos(self):
        for e in self.provas:
            self.assertEqual([q['numero'] for q in e['questoes']],list(range(1,len(e['questoes'])+1)))
            for q in e['questoes']:
                labels=''.join(a['letra'] for a in q['alternativas'])
                self.assertIn(labels,('CE','ABCD','ABCDE'))
                if q['anulada']:self.assertIsNone(q['gabarito'])
                else:self.assertIn(q['gabarito'],labels)
                self.assertTrue(q['enunciado'].strip())
                self.assertTrue(all(a['texto'].strip() for a in q['alternativas']))
                self.assertNotIn('JUSTIFICATIVA',q['enunciado'])
    def test_retificacoes_aplicadas(self):
        by={e['codigo'].split('-')[0]:e for e in self.provas}
        self.assertEqual(by['CAIXA']['caderno'],'PROVA 1 - GABARITO 1')
        self.assertEqual(by['CAIXA']['questoes'][0]['gabarito'],'A')
        self.assertTrue(by['CAMPINAS']['questoes'][46]['anulada'])
        self.assertEqual([q['numero'] for q in by['TJSP']['questoes'] if q['anulada']],[47,53,66,69])
        self.assertTrue(by['PF']['questoes'][25]['anulada'])
    def test_cadernos_locais_existem(self):
        for e in self.provas:
            q=e['questoes'][0]
            p=ROOT/'src/main/resources/static'/q['conteudo']['pdf'].split('#')[0].lstrip('/')
            self.assertTrue(p.read_bytes().startswith(b'%PDF'))

if __name__=='__main__':unittest.main()
