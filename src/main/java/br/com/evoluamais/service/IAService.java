package br.com.evoluamais.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class IAService {

    private final String apiKey;

    public IAService() {

        this.apiKey =
                System.getenv("OPENROUTER_API_KEY");

        if (apiKey == null || apiKey.isBlank()) {

            System.out.println(
                    "AVISO: variável OPENROUTER_API_KEY não configurada."
            );
        }
    }


    public String analisar(String pergunta) {

        if (apiKey == null || apiKey.isBlank()) {

            System.out.println(
                    "Não foi possível consultar a IA: chave da API não configurada."
            );

            return null;
        }


        String json = """
                {
                    "model": "openrouter/free",
                    "messages": [
                        {
                            "role": "user",
                            "content": "%s"
                        }
                    ]
                }
                """.formatted(pergunta);


        HttpRequest requisicao =
                HttpRequest.newBuilder()

                        .uri(
                                URI.create(
                                        "https://openrouter.ai/api/v1/chat/completions"
                                )
                        )

                        .header(
                                "Authorization",
                                "Bearer " + apiKey
                        )

                        .header(
                                "Content-Type",
                                "application/json"
                        )

                        .POST(
                                HttpRequest.BodyPublishers.ofString(json)
                        )

                        .build();


        try {

            HttpClient cliente =
                    HttpClient.newHttpClient();


            HttpResponse<String> resposta =
                    cliente.send(

                            requisicao,

                            HttpResponse.BodyHandlers.ofString()

                    );


            System.out.println(
                    "Status da API: "
                            + resposta.statusCode()
            );


            if (resposta.statusCode() != 200) {

                System.out.println(
                        "Erro da API:"
                );

                System.out.println(
                        resposta.body()
                );

                return null;
            }


            ObjectMapper mapper =
                    new ObjectMapper();


            JsonNode jsonResposta =
                    mapper.readTree(
                            resposta.body()
                    );


            String analise =
                    jsonResposta
                            .get("choices")
                            .get(0)
                            .get("message")
                            .get("content")
                            .asText();


            System.out.println(
                    "Resposta da IA:"
            );

            System.out.println(
                    analise
            );


            return analise;


        } catch (
                IOException |
                InterruptedException e
        ) {

            System.out.println(
                    "Erro ao consultar a IA:"
            );

            e.printStackTrace();

            return null;
        }
    }


    public String gerarRecomendacao(
            String disciplina,
            double percentualAcerto,
            String errosDetalhados) {


        String pergunta = """

                Você é o assistente educacional do aplicativo Evolua+.

                Um estudante está se preparando para uma prova.

                Disciplina: %s
                Percentual de acertos: %.2f%%

                Questões que o estudante errou:
                %s

                Analise o desempenho do estudante considerando
                o percentual de acertos e as questões erradas.

                Identifique os principais pontos que precisam ser
                estudados e forneça uma recomendação curta,
                objetiva e personalizada.

                Não informe a resposta correta das questões.
                Foque apenas em orientar os estudos.

                Responda em português.

                """.formatted(
                disciplina,
                percentualAcerto,
                errosDetalhados
        );


        return analisar(pergunta);
    }
}