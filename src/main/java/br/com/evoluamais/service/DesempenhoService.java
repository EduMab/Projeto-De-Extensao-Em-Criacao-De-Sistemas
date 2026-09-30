package br.com.evoluamais.service;

import br.com.evoluamais.model.Desempenho;
import br.com.evoluamais.model.DesempenhoResumo;
import br.com.evoluamais.model.Resposta;
import br.com.evoluamais.repository.DesempenhoRepository;
import br.com.evoluamais.repository.RespostaRepository;

import java.util.List;

public class DesempenhoService {

    private final DesempenhoRepository repository;
    private final IAService iaService;
    private final RecomendacaoIAService recomendacaoIAService;
    private final RespostaRepository respostaRepository;

    public DesempenhoService() {

        this.repository =
                new DesempenhoRepository();

        this.iaService =
                new IAService();

        this.recomendacaoIAService =
                new RecomendacaoIAService();

        this.respostaRepository =
                new RespostaRepository();
    }

    public String gerarRecomendacao(
            int idEstudante,
            int idProva,
            String disciplina) {

        double percentualAtual =
                calcularPercentual(
                        idEstudante,
                        idProva
                );

        Desempenho desempenho =
                repository.buscarPorEstudante(
                        idEstudante
                );

        if (desempenho == null) {
            return "Nenhum desempenho encontrado para este estudante.";
        }

        List<String> erros =
                respostaRepository.buscarErrosDetalhados(
                        idEstudante,
                        idProva
                );

        String errosTexto =
                String.join("\n", erros);

        String analise =
                iaService.gerarRecomendacao(
                        disciplina,
                        percentualAtual,
                        errosTexto
                );

        if (analise == null) {
            return "Não foi possível gerar a recomendação.";
        }

        recomendacaoIAService.salvarRecomendacao(
                idEstudante,
                analise
        );

        return analise;
    }

    public double calcularPercentual(
            int idEstudante,
            int idProva) {

        List<Resposta> respostas =
                respostaRepository.buscarPorEstudanteEProva(
                        idEstudante,
                        idProva
                );

        if (respostas.isEmpty()) {
            return 0;
        }

        int acertos = 0;

        for (Resposta resposta : respostas) {

            if (resposta.isAcertou()) {
                acertos++;
            }
        }

        double percentual =
                ((double) acertos / respostas.size()) * 100;

        repository.atualizarPercentual(
                idEstudante,
                percentual
        );

        return percentual;
    }

    public double obterPercentual(int idEstudante) {

        Desempenho desempenho =
                repository.buscarPorEstudante(
                        idEstudante
                );

        if (desempenho == null) {
            return 0;
        }

        return desempenho.getPercentualAcerto();
    }

    public int obterQuantidadeRespostas(int idEstudante) {

        List<Resposta> respostas =
                respostaRepository.buscarPorEstudante(
                        idEstudante
                );

        return respostas.size();
    }

    public int obterQuantidadeAcertos(int idEstudante) {

        List<Resposta> respostas =
                respostaRepository.buscarPorEstudante(
                        idEstudante
                );

        int acertos = 0;

        for (Resposta resposta : respostas) {

            if (resposta.isAcertou()) {
                acertos++;
            }
        }

        return acertos;
    }

    public int obterQuantidadeErros(int idEstudante) {

        List<Resposta> respostas =
                respostaRepository.buscarPorEstudante(
                        idEstudante
                );

        int erros = 0;

        for (Resposta resposta : respostas) {

            if (!resposta.isAcertou()) {
                erros++;
            }
        }

        return erros;
    }

    public DesempenhoResumo obterResumo(int idEstudante) {

        double percentual =
                obterPercentual(idEstudante);

        int respostas =
                obterQuantidadeRespostas(idEstudante);

        int acertos =
                obterQuantidadeAcertos(idEstudante);

        int erros =
                obterQuantidadeErros(idEstudante);

        DesempenhoResumo resumo =
                new DesempenhoResumo();

        resumo.setPercentual(percentual);
        resumo.setTotalRespostas(respostas);
        resumo.setAcertos(acertos);
        resumo.setErros(erros);

        return resumo;
    }
}