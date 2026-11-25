package br.com.evoluamais.controller;

import br.com.evoluamais.repository.ObjetivoRepository;
import org.junit.jupiter.api.*;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import java.sql.*;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class PerfilControllerTest {
    private String url;
    private MockMvc mvc;
    private MockHttpSession sessao;

    @BeforeEach void preparar() throws Exception {
        url = "jdbc:h2:mem:"+UUID.randomUUID()+";MODE=MySQL;DB_CLOSE_DELAY=-1";
        try(var c=DriverManager.getConnection(url);var s=c.createStatement()) {
            s.execute("CREATE TABLE usuario(id_usuario INT PRIMARY KEY,nome VARCHAR(100))");
            s.execute("CREATE TABLE prova(id_prova INT PRIMARY KEY,tipo VARCHAR(20),status_importacao VARCHAR(20),ano INT,codigo VARCHAR(160))");
            s.execute("CREATE TABLE estudante(id_estudante INT PRIMARY KEY,id_usuario INT,id_prova INT,objetivo_prova VARCHAR(20) DEFAULT NULL)");
            s.execute("INSERT INTO usuario VALUES(1,'Ana'),(2,'Bruno')");
            s.execute("INSERT INTO estudante(id_estudante,id_usuario,id_prova) VALUES(10,1,1),(20,2,1)");
        }
        mvc=novoCliente();sessao=new MockHttpSession();sessao.setAttribute("idEstudante",10);
    }

    private MockMvc novoCliente() {
        return MockMvcBuilders.standaloneSetup(new PerfilController(
                new ObjetivoRepository(()->DriverManager.getConnection(url)))).build();
    }

    @Test void primeiroAcessoNaoAssumeETECENomeVemDaConta() throws Exception {
        mvc.perform(get("/api/perfil?idEstudante=20").session(sessao))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control","no-store"))
                .andExpect(jsonPath("$.idEstudante").value(10)).andExpect(jsonPath("$.nome").value("Ana"))
                .andExpect(jsonPath("$.objetivo").isEmpty()).andExpect(jsonPath("$.objetivos.length()").value(4))
                .andExpect(jsonPath("$.objetivos[0].simuladoDisponivel").value(true))
                .andExpect(jsonPath("$.objetivos[1].simuladoDisponivel").value(false));
    }

    @Test void enemSoFicaDisponivelDepoisDaCargaCompletaSemMudarOutrosObjetivos() throws Exception {
        try(var c=DriverManager.getConnection(url);var s=c.createStatement()) {
            for(int i=0;i<19;i++)s.execute("INSERT INTO prova VALUES("+i+",'ENEM','VALIDADA',"+(2017+i/2)+",'ENEM-"+(2017+i/2)+"-DIA-"+(i%2+1)+"-AMARELO')");
        }
        mvc.perform(get("/api/perfil").session(sessao)).andExpect(jsonPath("$.objetivos[1].simuladoDisponivel").value(false));
        try(var c=DriverManager.getConnection(url);var s=c.createStatement()) {
            s.execute("INSERT INTO prova VALUES(19,'ENEM','VALIDADA',2026,'ENEM-2026-DIA-2-AMARELO')");
        }
        mvc.perform(get("/api/perfil").session(sessao)).andExpect(jsonPath("$.objetivos[1].simuladoDisponivel").value(true))
            .andExpect(jsonPath("$.objetivos[0].simuladoDisponivel").value(true));
    }

    @Test void salvaAsQuatroOpcoesNoBancoEPreservaEmOutraSessao() throws Exception {
        for(String objetivo:new String[]{"ETEC","ENEM","CONCURSO","FUVEST"}) {
            mvc.perform(put("/api/perfil/objetivo").session(sessao).header("X-Evolua-Request","perfil")
                    .contentType("application/json").content("{\"objetivo\":\""+objetivo+"\"}"))
                    .andExpect(status().isOk()).andExpect(jsonPath("$.objetivo").value(objetivo));
            var outroDispositivo=new MockHttpSession();outroDispositivo.setAttribute("idEstudante",10);
            novoCliente().perform(get("/api/perfil").session(outroDispositivo))
                    .andExpect(status().isOk()).andExpect(jsonPath("$.objetivo").value(objetivo));
        }
    }

    @Test void idEnviadoPeloClienteNaoAlteraContaDeOutroAluno() throws Exception {
        mvc.perform(put("/api/perfil/objetivo?idEstudante=20").session(sessao).header("X-Evolua-Request","perfil")
                .contentType("application/json").content("{\"objetivo\":\"ENEM\",\"idEstudante\":20}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.idEstudante").value(10));
        var bruno=new MockHttpSession();bruno.setAttribute("idEstudante",20);
        mvc.perform(get("/api/perfil").session(bruno)).andExpect(jsonPath("$.objetivo").isEmpty());
    }

    @Test void rejeitaEscolhasInvalidasSemMudarPreferencia() throws Exception {
        for(String json:new String[]{"{}","{\"objetivo\":null}","{\"objetivo\":\"TODOS\"}","{\"objetivo\":\"etec\"}"})
            mvc.perform(put("/api/perfil/objetivo").session(sessao).header("X-Evolua-Request","perfil")
                    .contentType("application/json").content(json)).andExpect(status().isBadRequest());
        mvc.perform(get("/api/perfil").session(sessao)).andExpect(jsonPath("$.objetivo").isEmpty());
    }

    @Test void exigeSessaoEHeaderNasAlteracoes() throws Exception {
        mvc.perform(get("/api/perfil")).andExpect(status().isUnauthorized());
        mvc.perform(put("/api/perfil/objetivo").header("X-Evolua-Request","perfil")
                .contentType("application/json").content("{\"objetivo\":\"ETEC\"}")).andExpect(status().isUnauthorized());
        mvc.perform(put("/api/perfil/objetivo").session(sessao)
                .contentType("application/json").content("{\"objetivo\":\"ETEC\"}")).andExpect(status().isForbidden());
        sessao.setAttribute("idEstudante",999);
        mvc.perform(get("/api/perfil").session(sessao)).andExpect(status().isUnauthorized());
    }
}
