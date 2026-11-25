package br.com.evoluamais.model;

public class RecomendacaoIA {

    private int idRecomendacao;
    private Estudante estudante;
    private String analise;
    private String dataRecomendacao;

    public RecomendacaoIA() {
    }

    public RecomendacaoIA(int idRecomendacao, Estudante estudante,
                          String analise, String dataRecomendacao) {
        this.idRecomendacao = idRecomendacao;
        this.estudante = estudante;
        this.analise = analise;
        this.dataRecomendacao = dataRecomendacao;
    }

    public int getIdRecomendacao() {
        return idRecomendacao;
    }

    public void setIdRecomendacao(int idRecomendacao) {
        this.idRecomendacao = idRecomendacao;
    }

    public Estudante getEstudante() {
        return estudante;
    }

    public void setEstudante(Estudante estudante) {
        this.estudante = estudante;
    }

    public String getAnalise() {
        return analise;
    }

    public void setAnalise(String analise) {
        this.analise = analise;
    }

    public String getDataRecomendacao() {
        return dataRecomendacao;
    }

    public void setDataRecomendacao(String dataRecomendacao) {
        this.dataRecomendacao = dataRecomendacao;
    }
}