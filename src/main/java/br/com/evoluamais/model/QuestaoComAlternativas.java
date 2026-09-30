package br.com.evoluamais.model;

import java.util.List;

public class QuestaoComAlternativas {

    private int idQuestao;
    private String enunciado;
    private String dificuldade;
    private List<Alternativa> alternativas;

    public QuestaoComAlternativas() {
    }

    public QuestaoComAlternativas(
            int idQuestao,
            String enunciado,
            String dificuldade,
            List<Alternativa> alternativas) {

        this.idQuestao = idQuestao;
        this.enunciado = enunciado;
        this.dificuldade = dificuldade;
        this.alternativas = alternativas;
    }

    public int getIdQuestao() {
        return idQuestao;
    }

    public void setIdQuestao(int idQuestao) {
        this.idQuestao = idQuestao;
    }

    public String getEnunciado() {
        return enunciado;
    }

    public void setEnunciado(String enunciado) {
        this.enunciado = enunciado;
    }

    public String getDificuldade() {
        return dificuldade;
    }

    public void setDificuldade(String dificuldade) {
        this.dificuldade = dificuldade;
    }

    public List<Alternativa> getAlternativas() {
        return alternativas;
    }

    public void setAlternativas(List<Alternativa> alternativas) {
        this.alternativas = alternativas;
    }
}