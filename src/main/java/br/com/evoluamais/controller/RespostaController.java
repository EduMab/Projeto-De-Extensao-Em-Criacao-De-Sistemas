package br.com.evoluamais.controller;

import br.com.evoluamais.model.Alternativa;
import br.com.evoluamais.repository.AlternativaRepository;
import br.com.evoluamais.repository.RespostaRepository;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/respostas")
public class RespostaController {

    private final RespostaRepository respostaRepository;
    private final AlternativaRepository alternativaRepository;

    public RespostaController() {

        this.respostaRepository =
                new RespostaRepository();

        this.alternativaRepository =
                new AlternativaRepository();
    }

    @PostMapping("/salvar")
    public String salvarResposta(
            @RequestParam int idEstudante,
            @RequestParam int idQuestao,
            @RequestParam int idAlternativa) {

        Alternativa alternativa =
                alternativaRepository.buscarPorId(
                        idAlternativa
                );

        if (alternativa == null) {

            return "Alternativa não encontrada.";
        }

        boolean acertou =
                alternativa.isCorreta();

        respostaRepository.salvarResposta(
                idEstudante,
                idQuestao,
                idAlternativa,
                acertou
        );

        return String.valueOf(acertou);
    }
}