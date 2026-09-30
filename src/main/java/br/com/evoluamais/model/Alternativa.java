package br.com.evoluamais.model;

public class Alternativa {

    private int idAlternativa;
    private String texto;
    private boolean correta;
    private Questao questao;

    public Alternativa() {
    }

    public Alternativa(int idAlternativa, String texto,
                       boolean correta, Questao questao) {
        this.idAlternativa = idAlternativa;
        this.texto = texto;
        this.correta = correta;
        this.questao = questao;
    }

    public int getIdAlternativa() {
        return idAlternativa;
    }

    public void setIdAlternativa(int idAlternativa) {
        this.idAlternativa = idAlternativa;
    }

    public String getTexto() {
        return texto;
    }

    public void setTexto(String texto) {
        this.texto = texto;
    }

    public boolean isCorreta() {
        return correta;
    }

    public void setCorreta(boolean correta) {
        this.correta = correta;
    }

    public Questao getQuestao() {
        return questao;
    }

    public void setQuestao(Questao questao) {
        this.questao = questao;
    }
}