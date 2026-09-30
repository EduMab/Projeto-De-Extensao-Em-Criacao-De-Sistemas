package br.com.evoluamais.service;

import br.com.evoluamais.model.Estudante;
import br.com.evoluamais.model.RecomendacaoIA;
import br.com.evoluamais.repository.RecomendacaoIARepository;

public class RecomendacaoIAService {

    private final RecomendacaoIARepository repository;

    public RecomendacaoIAService() {
        this.repository = new RecomendacaoIARepository();
    }

    public void salvarRecomendacao(int idEstudante, String analise) {

        Estudante estudante = new Estudante();
        estudante.setIdEstudante(idEstudante);

        RecomendacaoIA recomendacao = new RecomendacaoIA();
        recomendacao.setEstudante(estudante);
        recomendacao.setAnalise(analise);

        repository.salvar(recomendacao);
    }
}