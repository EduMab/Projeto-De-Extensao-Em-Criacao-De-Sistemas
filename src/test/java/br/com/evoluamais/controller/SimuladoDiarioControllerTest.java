package br.com.evoluamais.controller;

import br.com.evoluamais.repository.SimuladoDiarioRepository;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import java.time.*;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class SimuladoDiarioControllerTest {
    @Test void exigeSessaoEOrigemEUsaDataDeSaoPaulo() throws Exception {
        class RepositorioVerificado extends SimuladoDiarioRepository {
            int estudante;
            LocalDate dia;
            @Override public Map<String,Object> iniciar(int estudante, LocalDate dia) {
                this.estudante=estudante;this.dia=dia;return Map.of("id",123);
            }
        }
        var repo=new RepositorioVerificado();
        var controller=new SimuladoDiarioController(repo,Clock.fixed(Instant.parse("2026-11-24T01:00:00Z"),ZoneId.of("America/Sao_Paulo")));
        var mvc=MockMvcBuilders.standaloneSetup(controller).build();var sessao=new MockHttpSession();sessao.setAttribute("idEstudante",7);
        mvc.perform(post("/api/simulados-diarios/hoje").header("X-Evolua-Request","simulado")).andExpect(status().isUnauthorized());
        mvc.perform(post("/api/simulados-diarios/hoje").session(sessao)).andExpect(status().isForbidden());
        mvc.perform(post("/api/simulados-diarios/hoje?data=2099-01-01&idEstudante=99").session(sessao).header("X-Evolua-Request","simulado"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.id").value(123));
        assertEquals(7,repo.estudante);assertEquals(LocalDate.of(2026,11,23),repo.dia);
    }
}
