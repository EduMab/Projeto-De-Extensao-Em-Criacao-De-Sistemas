package br.com.evoluamais;

import br.com.evoluamais.model.Resposta;
import br.com.evoluamais.repository.RespostaRepository;

import java.util.List;

public class TesteRespostaRepository {

    public static void main(String[] args) {

        RespostaRepository repository =
                new RespostaRepository();

        List<Resposta> respostas =
                repository.buscarPorEstudante(1);

        System.out.println(
                "Quantidade de respostas encontradas: "
                        + respostas.size()
        );

        for (Resposta resposta : respostas) {

            System.out.println(
                    "Resposta ID: "
                            + resposta.getIdResposta()
                            + " | Acertou: "
                            + resposta.isAcertou()
            );
        }
    }
}