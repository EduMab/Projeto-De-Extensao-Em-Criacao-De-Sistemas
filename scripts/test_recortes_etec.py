"""Confere o índice publicado sem depender de downloads ou do banco."""
from pathlib import Path
import json,unittest,gzip
ROOT=Path(__file__).resolve().parents[1]

class RecortesEtecTest(unittest.TestCase):
 def test_todas_questoes_com_imagens_validas_e_sem_titulos_vizinhos(self):
  data=json.loads((ROOT/'acervo/etec/questoes.json').read_text())
  index=json.loads(gzip.decompress((ROOT/'src/main/resources/etec-recortes.json.gz').read_bytes()))
  self.assertEqual(len(index),790)
  for edition in data['edicoes']:
   code=edition['edicao']
   for q in edition['questoes']:
    with self.subTest(edicao=code,questao=q['numero']):
     row=index[f"{code}/{q['numero']}"];self.assertEqual(row['caixaTitulo'],q['conteudo']['caixaTitulo'])
     self.assertTrue(any(p['tipo']=='questao' for p in row['recortes']))
     for p in row['recortes']:
      self.assertTrue((ROOT/'src/main/resources/static'/p['imagem'].lstrip('/')).is_file())
      x,y,x2,y2=p['caixa'];self.assertTrue(0<=x<x2<=p['larguraPagina']);self.assertTrue(0<=y<y2<=p['alturaPagina'])
      for other in edition['questoes']:
       box=other['conteudo']['caixaTitulo'];cx=(box[0]+box[2])/2;cy=(box[1]+box[3])/2
       if other['conteudo']['pagina']==p['pagina'] and (other['numero']!=q['numero'] or p['tipo']=='apoio'):
        self.assertFalse(x<cx<x2 and y<cy<y2,f"Mostra título vizinho: {other['numero']}")
 def test_exemplo_santos_dumont_compartilha_apoio_mas_separa_32_e_33(self):
  index=json.loads(gzip.decompress((ROOT/'src/main/resources/etec-recortes.json.gz').read_bytes()))
  a=index['2026-2/32']['recortes'];b=index['2026-2/33']['recortes']
  self.assertEqual([p for p in a if p['tipo']=='apoio'],[p for p in b if p['tipo']=='apoio'])
  self.assertTrue(any(p['tipo']=='apoio' for p in a))
  self.assertNotEqual([p for p in a if p['tipo']=='questao'],[p for p in b if p['tipo']=='questao'])
 def test_gabaritos_e_alternativas_conferidos_na_geracao(self):
  report=json.loads((ROOT/'acervo/etec/validacao-recortes.json').read_text())
  self.assertEqual(report['total'],790)
  for edition in report['edicoes']:self.assertEqual(edition['alternativasPendentes'],[],edition['edicao'])
if __name__=='__main__':unittest.main()
