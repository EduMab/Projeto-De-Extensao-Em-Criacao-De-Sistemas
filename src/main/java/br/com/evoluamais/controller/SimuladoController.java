package br.com.evoluamais.controller;

import br.com.evoluamais.model.Desempenho;
import br.com.evoluamais.repository.DesempenhoRepository;
import br.com.evoluamais.service.DesempenhoService;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/simulado")
public class SimuladoController {

    private final DesempenhoService desempenhoService;
    private final DesempenhoRepository desempenhoRepository;

    public SimuladoController() {

        this.desempenhoService =
                new DesempenhoService();

        this.desempenhoRepository =
                new DesempenhoRepository();
    }

    @PostMapping("/finalizar")
    public Map<String, Object> finalizar(
            @RequestParam int idEstudante,
            @RequestParam int idProva,
            @RequestParam String disciplina) {

        String recomendacao =
                desempenhoService.gerarRecomendacao(
                        idEstudante,
                        idProva,
                        disciplina
                );

        Desempenho desempenho =
                desempenhoRepository.buscarPorEstudante(
                        idEstudante
                );

        double percentual = 0;

        if (desempenho != null) {

            percentual =
                    desempenho.getPercentualAcerto();
        }

        Map<String, Object> resposta =
                new HashMap<>();

        resposta.put(
                "percentual",
                percentual
        );

        resposta.put(
                "recomendacao",
                recomendacao
        );

        return resposta;
    }
}