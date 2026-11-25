package br.com.evoluamais.model;

public class DesempenhoResumo {

    private double percentual;
    private int totalRespostas;
    private int acertos;
    private int erros;

    public DesempenhoResumo() {
    }

    public DesempenhoResumo(double percentual,
                            int totalRespostas,
                            int acertos,
                            int erros) {

        this.percentual = percentual;
        this.totalRespostas = totalRespostas;
        this.acertos = acertos;
        this.erros = erros;
    }

    public double getPercentual() {
        return percentual;
    }

    public void setPercentual(double percentual) {
        this.percentual = percentual;
    }

    public int getTotalRespostas() {
        return totalRespostas;
    }

    public void setTotalRespostas(int totalRespostas) {
        this.totalRespostas = totalRespostas;
    }

    public int getAcertos() {
        return acertos;
    }

    public void setAcertos(int acertos) {
        this.acertos = acertos;
    }

    public int getErros() {
        return erros;
    }

    public void setErros(int erros) {
        this.erros = erros;
    }
}