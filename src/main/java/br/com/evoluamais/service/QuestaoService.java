package br.com.evoluamais.service;

import br.com.evoluamais.model.Alternativa;
import br.com.evoluamais.model.Questao;
import br.com.evoluamais.model.QuestaoComAlternativas;
import br.com.evoluamais.repository.AlternativaRepository;
import br.com.evoluamais.repository.QuestaoRepository;

import java.util.ArrayList;
import java.util.List;

public class QuestaoService {

    private final QuestaoRepository questaoRepository;
    private final AlternativaRepository alternativaRepository;

    public QuestaoService() {
        this.questaoRepository = new QuestaoRepository();
        this.alternativaRepository = new AlternativaRepository();
    }

    public List<QuestaoComAlternativas> buscarPorProva(int idProva) {

        List<Questao> questoes =
                questaoRepository.buscarPorProva(idProva);

        List<QuestaoComAlternativas> resultado =
                new ArrayList<>();

        for (Questao questao : questoes) {

            List<Alternativa> alternativas =
                    alternativaRepository.buscarPorQuestao(
                            questao.getIdQuestao()
                    );

            for (Alternativa alternativa : alternativas) {
                alternativa.setCorreta(false);
            }

            QuestaoComAlternativas questaoCompleta =
                    new QuestaoComAlternativas(
                            questao.getIdQuestao(),
                            questao.getEnunciado(),
                            questao.getDificuldade(),
                            alternativas
                    );

            resultado.add(questaoCompleta);
        }

        return resultado;
    }
}