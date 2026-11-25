package br.com.evoluamais.controller;

import br.com.evoluamais.model.QuestaoComAlternativas;
import br.com.evoluamais.service.QuestaoService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/questoes")
public class QuestaoController {

    private final QuestaoService questaoService;

    public QuestaoController() {
        this.questaoService = new QuestaoService();
    }

    @GetMapping("/prova/{idProva}")
    public List<QuestaoComAlternativas> buscarPorProva(
            @PathVariable int idProva) {

        return questaoService.buscarPorProva(idProva);
    }
}