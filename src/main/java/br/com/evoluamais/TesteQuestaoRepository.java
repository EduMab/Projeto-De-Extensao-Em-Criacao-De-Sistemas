package br.com.evoluamais;

import br.com.evoluamais.model.Questao;
import br.com.evoluamais.repository.QuestaoRepository;

import java.util.List;

public class TesteQuestaoRepository {

    public static void main(String[] args) {

        QuestaoRepository repository =
                new QuestaoRepository();

        List<Questao> questoes =
                repository.buscarPorProva(1);

        System.out.println("==============================");
        System.out.println("QUESTÕES DA PROVA");
        System.out.println("==============================");

        for (Questao questao : questoes) {

            System.out.println(
                    "Questão: "
                            + questao.getIdQuestao()
            );

            System.out.println(
                    "Enunciado: "
                            + questao.getEnunciado()
            );

            System.out.println(
                    "Dificuldade: "
                            + questao.getDificuldade()
            );

            System.out.println("------------------------------");
        }

        System.out.println(
                "Quantidade de questões: "
                        + questoes.size()
        );
    }
}