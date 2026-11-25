package br.com.evoluamais.model;

public class Prova {

    private int idProva;
    private String nome;
    private String descricao;

    public Prova() {
    }

    public Prova(int idProva, String nome, String descricao) {
        this.idProva = idProva;
        this.nome = nome;
        this.descricao = descricao;
    }

    public int getIdProva() {
        return idProva;
    }

    public void setIdProva(int idProva) {
        this.idProva = idProva;
    }

    public String getNome() {
        return nome;
    }

    public void setNome(String nome) {
        this.nome = nome;
    }

    public String getDescricao() {
        return descricao;
    }

    public void setDescricao(String descricao) {
        this.descricao = descricao;
    }
}