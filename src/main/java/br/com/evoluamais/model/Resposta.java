package br.com.evoluamais.model;

public class Resposta {

    private int idResposta;
    private Estudante estudante;
    private Questao questao;
    private Alternativa alternativa;
    private boolean acertou;
    private String dataResposta;

    public Resposta() {
    }

    public Resposta(int idResposta, Estudante estudante, Questao questao,
                    Alternativa alternativa, boolean acertou, String dataResposta) {
        this.idResposta = idResposta;
        this.estudante = estudante;
        this.questao = questao;
        this.alternativa = alternativa;
        this.acertou = acertou;
        this.dataResposta = dataResposta;
    }

    public int getIdResposta() {
        return idResposta;
    }

    public void setIdResposta(int idResposta) {
        this.idResposta = idResposta;
    }

    public Estudante getEstudante() {
        return estudante;
    }

    public void setEstudante(Estudante estudante) {
        this.estudante = estudante;
    }

    public Questao getQuestao() {
        return questao;
    }

    public void setQuestao(Questao questao) {
        this.questao = questao;
    }

    public Alternativa getAlternativa() {
        return alternativa;
    }

    public void setAlternativa(Alternativa alternativa) {
        this.alternativa = alternativa;
    }

    public boolean isAcertou() {
        return acertou;
    }

    public void setAcertou(boolean acertou) {
        this.acertou = acertou;
    }

    public String getDataResposta() {
        return dataResposta;
    }

    public void setDataResposta(String dataResposta) {
        this.dataResposta = dataResposta;
    }
}