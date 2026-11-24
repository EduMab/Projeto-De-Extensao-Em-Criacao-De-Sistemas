package br.com.evoluamais.controller;

import br.com.evoluamais.model.ObjetivoProva;
import br.com.evoluamais.repository.ObjetivoRepository;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import java.util.Map;

@RestController
@RequestMapping("/api/perfil")
public class PerfilController {
    private final ObjetivoRepository repository;
    public PerfilController(ObjetivoRepository repository) { this.repository = repository; }

    private int estudante(HttpSession session) {
        Object id = session.getAttribute("idEstudante");
        if (!(id instanceof Integer)) throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Entre na sua conta.");
        return (Integer) id;
    }

    @GetMapping
    public ResponseEntity<Map<String, Object>> perfil(HttpSession session) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(repository.perfil(estudante(session)));
    }

    public record Escolha(String objetivo) {}

    @PutMapping("/objetivo")
    public ResponseEntity<Map<String, Object>> salvar(@RequestBody Escolha escolha, HttpSession session,
            @RequestHeader(value="X-Evolua-Request", required=false) String origem) {
        int id = estudante(session);
        if (!"perfil".equals(origem)) throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Requisição inválida.");
        var objetivo = ObjetivoProva.validar(escolha.objetivo());
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(repository.salvar(id, objetivo));
    }
}
