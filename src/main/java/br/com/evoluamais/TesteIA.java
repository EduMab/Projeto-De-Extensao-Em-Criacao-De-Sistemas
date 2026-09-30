package br.com.evoluamais;

import br.com.evoluamais.service.IAService;

public class TesteIA {

    public static void main(String[] args) {

        IAService iaService = new IAService();

        String resposta = iaService.gerarRecomendacao(
                "Matemática",
                60,
                """
                - Questão 3 | Disciplina: Matemática | Dificuldade: Fácil | Enunciado: Qual é o resultado de 10 - 3?
                - Questão 5 | Disciplina: Matemática | Dificuldade: Médio | Enunciado: Qual é a raiz quadrada de 81?
                """
        );
        System.out.println("=================================");
        System.out.println("RECOMENDAÇÃO:");
        System.out.println(resposta);
        System.out.println("=================================");
    }
}