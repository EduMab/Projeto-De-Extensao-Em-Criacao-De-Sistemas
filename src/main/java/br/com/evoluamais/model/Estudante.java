package br.com.evoluamais.model;

public class Estudante {

    private int idEstudante;
    private Usuario usuario;
    private Prova prova;

    public Estudante() {
    }

    public Estudante(int idEstudante, Usuario usuario, Prova prova) {
        this.idEstudante = idEstudante;
        this.usuario = usuario;
        this.prova = prova;
    }

    public int getIdEstudante() {
        return idEstudante;
    }

    public void setIdEstudante(int idEstudante) {
        this.idEstudante = idEstudante;
    }

    public Usuario getUsuario() {
        return usuario;
    }

    public void setUsuario(Usuario usuario) {
        this.usuario = usuario;
    }

    public Prova getProva() {
        return prova;
    }

    public void setProva(Prova prova) {
        this.prova = prova;
    }
}