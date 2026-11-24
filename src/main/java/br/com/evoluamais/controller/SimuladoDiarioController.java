package br.com.evoluamais.controller;

import br.com.evoluamais.repository.SimuladoDiarioRepository;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import java.time.*;
import java.util.*;

@RestController
@RequestMapping({"/api/simulados-semanais", "/api/simulados-diarios"})
public class SimuladoDiarioController {
    private final SimuladoDiarioRepository repository;
    private final Clock clock;
    @org.springframework.beans.factory.annotation.Autowired
    public SimuladoDiarioController(SimuladoDiarioRepository repository) {
        this(repository, Clock.system(ZoneId.of("America/Sao_Paulo")));
    }
    SimuladoDiarioController(SimuladoDiarioRepository repository, Clock clock) { this.repository = repository; this.clock = clock; }
    private int estudante(HttpSession session) {
        Object id = session.getAttribute("idEstudante");
        if (!(id instanceof Integer)) throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Faca login para acessar seus simulados.");
        return (Integer) id;
    }
    private void origem(String header) {
        if (!"simulado".equals(header)) throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Requisicao invalida.");
    }
    @GetMapping("/acervo") public Map<String, Object> acervo(@RequestParam(defaultValue="ETEC") String tipo) { return repository.acervo(tipo); }
    // As rotas antigas tambem obedecem ao intervalo semanal.
    @PostMapping({"/atual", "/hoje"}) public Map<String, Object> hoje(HttpSession session, @RequestHeader(value="X-Evolua-Request", required=false) String header) {
        int id = estudante(session); origem(header); return repository.iniciar(id, LocalDate.now(clock));
    }
    @GetMapping("/historico") public List<Map<String, Object>> historico(HttpSession session) { return repository.historico(estudante(session)); }
    @GetMapping("/{id}") public Map<String, Object> obter(@PathVariable long id, HttpSession session) { return repository.obter(estudante(session), id); }
    public record Resposta(int idAlternativa) {}
    @PutMapping("/{id}/questoes/{posicao}/resposta") public Map<String, Boolean> responder(@PathVariable long id, @PathVariable int posicao,
            @RequestBody Resposta resposta, HttpSession session, @RequestHeader(value="X-Evolua-Request", required=false) String header) {
        int estudante = estudante(session); origem(header); repository.responder(estudante, id, posicao, resposta.idAlternativa()); return Map.of("salva", true);
    }
    @PostMapping("/{id}/finalizar") public Map<String, Object> finalizar(@PathVariable long id, HttpSession session,
            @RequestHeader(value="X-Evolua-Request", required=false) String header) {
        int estudante = estudante(session); origem(header); return repository.finalizar(estudante, id);
    }
}
