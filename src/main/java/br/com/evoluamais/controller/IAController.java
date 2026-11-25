package br.com.evoluamais.controller;

import br.com.evoluamais.service.DesempenhoService;
import org.springframework.web.bind.annotation.*;
import br.com.evoluamais.model.DesempenhoResumo;



@RestController
@RequestMapping("/ia")
public class IAController {

    private final DesempenhoService desempenhoService;

    public IAController() {
        this.desempenhoService = new DesempenhoService();
    }

    @GetMapping("/recomendacao/{idEstudante}")
    public String gerarRecomendacao(
            @PathVariable int idEstudante,
            @RequestParam int idProva,
            @RequestParam String disciplina) {

        return desempenhoService.gerarRecomendacao(
                idEstudante,
                idProva,
                disciplina
        );
    }

    @GetMapping("/desempenho/{idEstudante}")
    public double obterDesempenho(
            @PathVariable int idEstudante) {

        return desempenhoService.obterPercentual(idEstudante);
    }

    @GetMapping("/respostas/{idEstudante}")
    public int obterQuantidadeRespostas(
            @PathVariable int idEstudante) {

        return desempenhoService.obterQuantidadeRespostas(
                idEstudante
        );
    }
    @GetMapping("/acertos/{idEstudante}")
    public int obterQuantidadeAcertos(
            @PathVariable int idEstudante) {

        return desempenhoService.obterQuantidadeAcertos(
                idEstudante
        );
    }
    @GetMapping("/erros/{idEstudante}")
    public int obterQuantidadeErros(
            @PathVariable int idEstudante) {

        return desempenhoService.obterQuantidadeErros(
                idEstudante
        );
    }
    @GetMapping("/resumo/{idEstudante}")
    public DesempenhoResumo obterResumo(
            @PathVariable int idEstudante) {

        return desempenhoService.obterResumo(idEstudante);
    }
}