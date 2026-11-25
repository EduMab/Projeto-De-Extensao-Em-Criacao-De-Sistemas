package br.com.evoluamais;

import br.com.evoluamais.model.Alternativa;
import br.com.evoluamais.repository.AlternativaRepository;

import java.util.List;

public class TesteAlternativaRepository {

    public static void main(String[] args) {

        AlternativaRepository repository =
                new AlternativaRepository();

        List<Alternativa> alternativas =
                repository.buscarPorQuestao(3);

        System.out.println("==============================");
        System.out.println("ALTERNATIVAS DA QUESTÃO 3");
        System.out.println("==============================");

        for (Alternativa alternativa : alternativas) {

            System.out.println(
                    "ID: "
                            + alternativa.getIdAlternativa()
            );

            System.out.println(
                    "Texto: "
                            + alternativa.getTexto()
            );

            System.out.println(
                    "Correta: "
                            + alternativa.isCorreta()
            );

            System.out.println("------------------------------");
        }

        System.out.println(
                "Quantidade de alternativas: "
                        + alternativas.size()
        );
    }
}