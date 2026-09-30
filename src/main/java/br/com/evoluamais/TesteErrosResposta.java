package br.com.evoluamais;

import br.com.evoluamais.repository.RespostaRepository;

import java.util.List;

public class TesteErrosResposta {

    public static void main(String[] args) {

        RespostaRepository repository =
                new RespostaRepository();

        int idEstudante = 1;
        int idProva = 1;

        List<String> erros =
                repository.buscarErrosDetalhados(
                        idEstudante,
                        idProva
                );

        System.out.println("=================================");
        System.out.println("QUESTÕES ERRADAS:");
        System.out.println("=================================");

        for (String erro : erros) {
            System.out.println(erro);
        }

        System.out.println("=================================");
        System.out.println(
                "Quantidade de erros: " + erros.size()
        );
    }
}