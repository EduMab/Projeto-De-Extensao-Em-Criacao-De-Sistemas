package br.com.evoluamais;

import br.com.evoluamais.service.DesempenhoService;

public class TesteDesempenhoService {

    public static void main(String[] args) {

        DesempenhoService service =
                new DesempenhoService();

        String recomendacao =
                service.gerarRecomendacao(
                        1,
                        1,
                        "Matemática"
                );
        System.out.println("=================================");
        System.out.println("RECOMENDAÇÃO DO EVOLUA+:");
        System.out.println(recomendacao);
        System.out.println("=================================");
    }
}