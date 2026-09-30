package br.com.evoluamais.model;

public class Desempenho {

    private int idDesempenho;
    private Estudante estudante;
    private Disciplina disciplina;
    private double percentualAcerto;

    public Desempenho() {
    }

    public Desempenho(int idDesempenho, Estudante estudante,
                      Disciplina disciplina, double percentualAcerto) {
        this.idDesempenho = idDesempenho;
        this.estudante = estudante;
        this.disciplina = disciplina;
        this.percentualAcerto = percentualAcerto;
    }

    public int getIdDesempenho() {
        return idDesempenho;
    }

    public void setIdDesempenho(int idDesempenho) {
        this.idDesempenho = idDesempenho;
    }

    public Estudante getEstudante() {
        return estudante;
    }

    public void setEstudante(Estudante estudante) {
        this.estudante = estudante;
    }

    public Disciplina getDisciplina() {
        return disciplina;
    }

    public void setDisciplina(Disciplina disciplina) {
        this.disciplina = disciplina;
    }

    public double getPercentualAcerto() {
        return percentualAcerto;
    }

    public void setPercentualAcerto(double percentualAcerto) {
        this.percentualAcerto = percentualAcerto;
    }
}