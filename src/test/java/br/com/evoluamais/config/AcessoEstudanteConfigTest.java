package br.com.evoluamais.config;

import org.junit.jupiter.api.*;
import org.springframework.context.annotation.*;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.mock.web.MockServletContext;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class AcessoEstudanteConfigTest {
    private AnnotationConfigWebApplicationContext context;
    private MockMvc mvc;
    private MockHttpSession session;

    @Configuration
    @EnableWebMvc
    @Import(AcessoEstudanteConfig.class)
    static class AplicacaoTeste {
        @Bean RotasTeste rotas() { return new RotasTeste(); }
    }

    @RestController
    static class RotasTeste {
        @GetMapping("/ia/desempenho/{idEstudante}") String desempenho(@PathVariable int idEstudante) { return "permitido"; }
        @PostMapping({"/respostas/salvar", "/simulado/finalizar"}) String salvar(@RequestParam int idEstudante) { return "permitido"; }
        @GetMapping("/usuarios/teste") String saude() { return "ok"; }
    }

    @BeforeEach void preparar() {
        context = new AnnotationConfigWebApplicationContext();
        context.setServletContext(new MockServletContext());
        context.register(AplicacaoTeste.class); context.refresh();
        mvc = MockMvcBuilders.webAppContextSetup(context).build();
        session = new MockHttpSession(); session.setAttribute("idEstudante", 7);
    }
    @AfterEach void fechar() { context.close(); }

    @Test void exigeLoginNasRotasLegadas() throws Exception {
        mvc.perform(get("/ia/desempenho/7")).andExpect(status().isUnauthorized());
        for (String rota : new String[]{"/respostas/salvar", "/simulado/finalizar"}) {
            mvc.perform(post(rota).param("idEstudante", "7")).andExpect(status().isUnauthorized());
        }
    }
    @Test void impedeAcessoAOutroEstudante() throws Exception {
        mvc.perform(get("/ia/desempenho/8").session(session)).andExpect(status().isForbidden());
        for (String rota : new String[]{"/respostas/salvar", "/simulado/finalizar"}) {
            mvc.perform(post(rota).session(session).param("idEstudante", "8")).andExpect(status().isForbidden());
        }
    }
    @Test void permiteAcessoAPropriaConta() throws Exception {
        mvc.perform(get("/ia/desempenho/7").session(session)).andExpect(status().isOk()).andExpect(content().string("permitido"));
        for (String rota : new String[]{"/respostas/salvar", "/simulado/finalizar"}) {
            mvc.perform(post(rota).session(session).param("idEstudante", "7")).andExpect(status().isOk());
        }
    }
    @Test void parametrosNaoDisfarcamOutroIdNoCaminho() throws Exception {
        mvc.perform(get("/ia/desempenho/8?idEstudante=7").session(session)).andExpect(status().isForbidden());
        mvc.perform(post("/respostas/salvar").session(session).param("idEstudante", "7", "8")).andExpect(status().isForbidden());
    }
    @Test void rejeitaIdentificadorAusenteOuInvalido() throws Exception {
        mvc.perform(post("/respostas/salvar").session(session)).andExpect(status().isBadRequest());
        mvc.perform(get("/ia/desempenho/invalido").session(session)).andExpect(status().isBadRequest());
    }
    @Test void mantemHealthCheckPublico() throws Exception {
        mvc.perform(get("/usuarios/teste")).andExpect(status().isOk()).andExpect(content().string("ok"));
    }
}
