"""Verifica a hospedagem de destino antes de qualquer acesso ao banco."""
import os
import unittest
from unittest.mock import patch, MagicMock
from importar_enem import origem_publicacao, publicacao
from importar_concursos import ImportacaoError


class PublicacaoEnemTest(unittest.TestCase):
    def test_origem_obrigatoria_sem_fallback_para_outra_hospedagem(self):
        with patch.dict(os.environ, {}, clear=True), patch('urllib.request.urlopen') as abrir:
            with self.assertRaises(ImportacaoError):
                publicacao([])
            abrir.assert_not_called()

    def test_aceita_origem_railway_e_desenvolvimento_local(self):
        self.assertEqual(origem_publicacao(' https://exemplo.up.railway.app/ '),
                         'https://exemplo.up.railway.app')
        self.assertEqual(origem_publicacao('http://localhost:8080'), 'http://localhost:8080')

    def test_rejeita_credenciais_caminho_query_e_http_remoto(self):
        for origem in ('', 'http://exemplo.up.railway.app', 'https://user:senha@exemplo.com',
                       'https://exemplo.com/index.html', 'https://exemplo.com?token=x',
                       'https://exemplo.com#x', 'https://exemplo.com:invalida'):
            with self.subTest(origem=origem), self.assertRaises(ImportacaoError):
                origem_publicacao(origem)

    def test_script_e_imagens_sao_verificados_na_mesma_origem(self):
        resposta=MagicMock()
        resposta.__enter__.return_value=resposta
        resposta.read.return_value=b'function escolherIdiomaEnem() {} // (concursos|enem)'
        resposta.status=200
        resposta.headers={'content-type':'image/webp'}
        origem='https://exemplo.up.railway.app'
        imagem='/questoes/enem/enem-2026-dia-1-amarelo/001-ingles.webp'
        with patch.dict(os.environ, {'EVOLUA_PUBLIC_URL':origem}), \
                patch('urllib.request.urlopen', return_value=resposta) as abrir:
            publicacao([imagem])
        self.assertEqual(abrir.call_args_list[0].args[0], origem+'/simulados.js')
        pedido=abrir.call_args_list[1].args[0]
        self.assertEqual(pedido.full_url, origem+imagem)
        self.assertEqual(pedido.get_method(), 'HEAD')

    def test_suporte_enem_ausente_impede_publicacao(self):
        resposta=MagicMock()
        resposta.__enter__.return_value=resposta
        resposta.read.return_value=b'// versao antiga'
        with patch('urllib.request.urlopen', return_value=resposta), self.assertRaises(ImportacaoError):
            publicacao([], origem='https://exemplo.up.railway.app')


if __name__=='__main__':
    unittest.main()
