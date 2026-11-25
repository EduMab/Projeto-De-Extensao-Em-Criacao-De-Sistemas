package br.com.evoluamais.model;

public class Questao {

    private int idQuestao;
    private String enunciado;
    private String dificuldade;
    private Disciplina disciplina;
    private Prova prova;

    public Questao() {
    }

    public Questao(int idQuestao, String enunciado, String dificuldade,
                   Disciplina disciplina, Prova prova) {
        this.idQuestao = idQuestao;
        this.enunciado = enunciado;
        this.dificuldade = dificuldade;
        this.disciplina = disciplina;
        this.prova = prova;
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

    public Disciplina getDisciplina() {
        return disciplina;
    }

    public void setDisciplina(Disciplina disciplina) {
        this.disciplina = disciplina;
    }

    public Prova getProva() {
        return prova;
    }

    public void setProva(Prova prova) {
        this.prova = prova;
    }
}