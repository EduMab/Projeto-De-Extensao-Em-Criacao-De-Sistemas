package br.com.evoluamais.controller;

import br.com.evoluamais.repository.NotificacaoRepository;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;

@RestController
@RequestMapping("/api/notificacoes")
public class NotificacaoController {
    private final NotificacaoRepository repository;
    public NotificacaoController(NotificacaoRepository repository) { this.repository = repository; }

    private int estudante(HttpSession session) {
        Object id = session.getAttribute("idEstudante");
        if (!(id instanceof Integer))
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED,"Faça login para acessar suas notificações.");
        return (Integer) id;
    }

    @GetMapping
    public Map<String,Object> listar(HttpSession session) {
        return repository.listar(estudante(session));
    }

    @PostMapping("/{id}/lida")
    public Map<String,Boolean> marcarLida(@PathVariable long id, HttpSession session) {
        repository.marcarLida(estudante(session),id);
        return Map.of("sucesso",true);
    }

    @PostMapping("/lidas")
    public Map<String,Boolean> marcarTodasLidas(HttpSession session) {
        repository.marcarTodasLidas(estudante(session));
        return Map.of("sucesso",true);
    }
}
