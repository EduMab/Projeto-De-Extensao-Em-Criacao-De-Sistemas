package br.com.evoluamais;

import br.com.evoluamais.service.DesempenhoService;

public class TesteCalculoDesempenho {

    public static void main(String[] args) {

        DesempenhoService service =
                new DesempenhoService();

        double percentual =
                service.calcularPercentual(1, 1);

        System.out.println(
                "Percentual de acerto calculado: "
                        + percentual
                        + "%"
        );
    }
}