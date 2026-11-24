package br.com.evoluamais.model;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

public enum ObjetivoProva {
    ETEC("ETEC", "Ensino técnico e médio", true),
    ENEM("ENEM", "Seu caminho para a faculdade", false),
    CONCURSO("Concurso público", "Preparação para a carreira pública", false),
    FUVEST("FUVEST", "Preparação para a USP", false);

    private final String nome;
    private final String descricao;
    private final boolean simuladoDisponivel;

    ObjetivoProva(String nome, String descricao, boolean simuladoDisponivel) {
        this.nome = nome;
        this.descricao = descricao;
        this.simuladoDisponivel = simuladoDisponivel;
    }

    public String nome() { return nome; }
    public String descricao() { return descricao; }
    public boolean simuladoDisponivel() { return simuladoDisponivel; }

    public static ObjetivoProva validar(String codigo) {
        try { return valueOf(codigo == null ? "" : codigo); }
        catch (IllegalArgumentException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                    "Escolha ETEC, ENEM, Concurso público ou FUVEST.");
        }
    }
}
