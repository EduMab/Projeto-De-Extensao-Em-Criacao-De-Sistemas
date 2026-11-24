package br.com.evoluamais.repository;

import com.fasterxml.jackson.databind.JsonNode;
import org.junit.jupiter.api.*;
import org.springframework.web.server.ResponseStatusException;
import java.sql.*;
import java.time.LocalDate;
import java.util.*;
import java.util.concurrent.*;
import static org.junit.jupiter.api.Assertions.*;

class SimuladoDiarioRepositoryTest {
    private String url;
    private SimuladoDiarioRepository repo;
    private final LocalDate hoje = LocalDate.of(2026, 11, 23);
    @BeforeEach void preparar() throws Exception {
        url = "jdbc:h2:mem:" + UUID.randomUUID() + ";MODE=MySQL;DB_CLOSE_DELAY=-1;LOCK_TIMEOUT=15000";
        repo = new SimuladoDiarioRepository(() -> DriverManager.getConnection(url));
        try (var c = DriverManager.getConnection(url); var s = c.createStatement()) {
            s.execute("CREATE TABLE estudante(id_estudante INT PRIMARY KEY,objetivo_prova VARCHAR(20))");
            s.execute("INSERT INTO estudante VALUES(1,'ETEC'),(2,'ETEC')");
            s.execute("CREATE TABLE prova(id_prova INT PRIMARY KEY,nome VARCHAR(100),codigo VARCHAR(160),edicao VARCHAR(80),tipo VARCHAR(20),status_importacao VARCHAR(20))");
            s.execute("CREATE TABLE questao(id_questao INT PRIMARY KEY,id_prova INT,numero_original INT,enunciado CLOB,anulada INT,conteudo_json CLOB)");
            s.execute("CREATE TABLE alternativa(id_alternativa INT PRIMARY KEY,id_questao INT,letra CHAR(1),texto VARCHAR(100),correta INT)");
            s.execute("CREATE TABLE resposta(id_questao INT,id_estudante INT,data_resposta TIMESTAMP)");
            s.execute("CREATE TABLE simulado_diario(id_simulado BIGINT AUTO_INCREMENT PRIMARY KEY,id_estudante INT,tipo VARCHAR(20),data_simulado DATE,concluido_em TIMESTAMP,UNIQUE(id_estudante,tipo,data_simulado))");
            s.execute("CREATE TABLE simulado_diario_questao(id_simulado BIGINT,posicao INT,id_questao INT,snapshot_json CLOB,id_alternativa INT,acertou INT,respondida_em TIMESTAMP,PRIMARY KEY(id_simulado,posicao),UNIQUE(id_simulado,id_questao))");
            for (int i=1;i<=4;i++) s.execute("INSERT INTO prova VALUES("+i+",'ETEC','ETEC-"+i+"','"+i+"','ETEC','VALIDADA')");
            for (int i=1;i<=80;i++) {
                s.execute("INSERT INTO questao VALUES("+i+","+((i-1)/20+1)+","+i+",'Texto original',0,'{\"modo\":\"pagina_original\",\"pagina\":2,\"paginas\":[]}')");
                for (int a=0;a<5;a++) s.execute("INSERT INTO alternativa VALUES("+(i*10+a)+","+i+",'"+(char)('A'+a)+"','Alternativa',"+(a==0?1:0)+")");
            }
        }
    }
    @SuppressWarnings("unchecked") private List<JsonNode> questoes(Map<String,Object> simulado) { return (List<JsonNode>)simulado.get("questoes"); }
    private Set<Integer> ids(Map<String,Object> simulado) { var ids=new HashSet<Integer>();questoes(simulado).forEach(q->ids.add(q.get("idQuestao").asInt()));return ids; }

    @Test void mesclaEdicoesRetomaSemanaEUsaIneditasAntesDeRepetir() {
        var um=repo.iniciar(1,hoje);var retomado=repo.iniciar(1,hoje.plusDays(6));var dois=repo.iniciar(1,hoje.plusWeeks(1));var tres=repo.iniciar(1,hoje.plusWeeks(2));
        assertEquals(7,um.get("intervaloDias"));assertEquals("2026-11-30",um.get("proximaLiberacao"));
        assertEquals(40,ids(um).size());assertEquals(um,retomado);assertTrue(Collections.disjoint(ids(um),ids(dois)));assertEquals(ids(um),ids(tres));
        assertEquals(4,questoes(um).stream().map(q->q.get("edicao").asText()).distinct().count());
        assertTrue(questoes(um).stream().allMatch(q->!q.has("gabarito")&&!q.has("acertou")));assertFalse(um.containsKey("acertos"));
        assertEquals(3,repo.historico(1).size());assertTrue(repo.historico(2).isEmpty());
    }
    @Test void chamadasSimultaneasRecebemAMesmaSelecao() throws Exception {
        repo.iniciar(1,hoje.minusWeeks(1));
        try(var executor=Executors.newVirtualThreadPerTaskExecutor()) {
            var gate=new CountDownLatch(1);
            var a=executor.submit(()->{gate.await();return repo.iniciar(1,hoje);});
            var b=executor.submit(()->{gate.await();return repo.iniciar(1,hoje);});gate.countDown();
            assertEquals(a.get(20,TimeUnit.SECONDS),b.get(20,TimeUnit.SECONDS));assertEquals(2,repo.historico(1).size());
        }
    }
    @Test void retomaRespostasNosSeisDiasSeguintesEIsolaEstudantes() {
        var primeira=repo.iniciar(1,hoje);
        long id=((Number)primeira.get("id")).longValue();
        int alternativa=questoes(primeira).get(0).get("alternativas").get(1).get("id").asInt();
        repo.responder(1,id,1,alternativa);
        var salva=repo.obter(1,id);
        for(int dias=1;dias<=6;dias++) assertEquals(salva,repo.iniciar(1,hoje.plusDays(dias)));
        assertEquals(1,salva.get("respondidas"));
        assertEquals(alternativa,questoes(salva).get(0).get("alternativaSelecionada").asInt());
        assertEquals(1,repo.historico(1).size());
        assertNotEquals(id,repo.iniciar(2,hoje.plusDays(1)).get("id"));
        var proxima=repo.iniciar(1,hoje.plusDays(7));
        assertNotEquals(id,proxima.get("id"));
        assertEquals(0,proxima.get("respondidas"));
        assertEquals(salva,repo.obter(1,id));
    }
    @Test void concluirNaoAntecipaLiberacaoSemanal() {
        var primeira=repo.iniciar(1,hoje);long id=((Number)primeira.get("id")).longValue();
        for(var q:questoes(primeira)) repo.responder(1,id,q.get("posicao").asInt(),q.get("alternativas").get(0).get("id").asInt());
        var concluida=repo.finalizar(1,id);
        for(int dias=0;dias<=6;dias++) assertEquals(concluida,repo.iniciar(1,hoje.plusDays(dias)));
        assertNotEquals(id,repo.iniciar(1,hoje.plusDays(7)).get("id"));
        assertEquals(concluida,repo.obter(1,id));
    }
    @Test void preservaHistoricoDiarioLegadoERetomaSelecaoMaisRecente() throws Exception {
        var antiga=repo.iniciar(1,hoje.minusDays(2));long idAntiga=((Number)antiga.get("id")).longValue();
        long idRecente;
        try(var c=DriverManager.getConnection(url)) {
            try(var s=c.prepareStatement("INSERT INTO simulado_diario(id_estudante,tipo,data_simulado) VALUES(1,'ETEC',?)",Statement.RETURN_GENERATED_KEYS)) {
                s.setDate(1,java.sql.Date.valueOf(hoje.minusDays(1)));s.executeUpdate();
                try(var r=s.getGeneratedKeys()){assertTrue(r.next());idRecente=r.getLong(1);}
            }
            try(var s=c.prepareStatement("INSERT INTO simulado_diario_questao(id_simulado,posicao,id_questao,snapshot_json) SELECT ?,posicao,id_questao,snapshot_json FROM simulado_diario_questao WHERE id_simulado=?")) {
                s.setLong(1,idRecente);s.setLong(2,idAntiga);s.executeUpdate();
            }
        }
        assertEquals(idRecente,repo.iniciar(1,hoje).get("id"));
        assertEquals(idRecente,repo.iniciar(1,hoje.plusDays(5)).get("id"));
        assertEquals(2,repo.historico(1).size());
        assertEquals(antiga,repo.obter(1,idAntiga));
        assertNotEquals(idRecente,repo.iniciar(1,hoje.plusDays(6)).get("id"));
        assertEquals(3,repo.historico(1).size());
    }
    @Test void publicaMetadadosSemanaisDoAcervo() {
        var acervo=repo.acervo();
        assertEquals(40,acervo.get("questoesPorSimulado"));
        assertEquals(7,acervo.get("intervaloDias"));
        assertEquals(2,acervo.get("semanasCom40Ineditas"));
        assertFalse(acervo.containsKey("questoesPorDia"));
        assertFalse(acervo.containsKey("diasCom40Ineditas"));
    }
    @Test void exigeObjetivoETECETrocarNaoApagaNemAntecipaSimulado() throws Exception {
        var primeiro = repo.iniciar(1,hoje);
        long id = ((Number)primeiro.get("id")).longValue();
        for (String objetivo : new String[]{null,"ENEM","FUVEST"}) {
            try (var c=DriverManager.getConnection(url);var s=c.prepareStatement("UPDATE estudante SET objetivo_prova=? WHERE id_estudante=1")) {
                s.setString(1,objetivo);s.executeUpdate();
            }
            assertEquals(409,assertThrows(ResponseStatusException.class,()->repo.iniciar(1,hoje)).getStatusCode().value());
            assertEquals(1,repo.historico(1).size());
            assertEquals(primeiro,repo.obter(1,id));
        }
        try(var c=DriverManager.getConnection(url);var s=c.createStatement()){s.execute("UPDATE estudante SET objetivo_prova='ETEC' WHERE id_estudante=1");}
        assertEquals(primeiro,repo.iniciar(1,hoje.plusDays(6)));
    }
    @Test void verificaDonoAlternativaEConclusaoECalculaNotaComSnapshot() throws Exception {
        var simulado=repo.iniciar(1,hoje);long id=((Number)simulado.get("id")).longValue();var qs=questoes(simulado);
        assertEquals(404,assertThrows(ResponseStatusException.class,()->repo.obter(2,id)).getStatusCode().value());
        assertEquals(404,assertThrows(ResponseStatusException.class,()->repo.responder(2,id,1,10)).getStatusCode().value());
        assertEquals(400,assertThrows(ResponseStatusException.class,()->repo.responder(1,id,1,qs.get(1).get("alternativas").get(0).get("id").asInt())).getStatusCode().value());
        assertEquals(409,assertThrows(ResponseStatusException.class,()->repo.finalizar(1,id)).getStatusCode().value());
        // Edicao posterior do banco nao altera o gabarito congelado desta tentativa.
        try(var c=DriverManager.getConnection(url);var s=c.createStatement()){s.execute("UPDATE alternativa SET correta=0");}
        for(var q:qs) repo.responder(1,id,q.get("posicao").asInt(),q.get("alternativas").get(0).get("id").asInt());
        var finalizado=repo.finalizar(1,id);assertEquals(40,finalizado.get("acertos"));assertEquals(100.0,finalizado.get("percentual"));
        assertEquals(finalizado,repo.finalizar(1,id));assertTrue(questoes(finalizado).stream().allMatch(q->q.get("gabarito").asText().equals("A")));
        assertEquals(409,assertThrows(ResponseStatusException.class,()->repo.responder(1,id,1,10)).getStatusCode().value());
    }
    @Test void excluiAnuladasRascunhosEGabaritosInvalidosSemCriarParcial() throws Exception {
        try(var c=DriverManager.getConnection(url);var s=c.createStatement()) {
            s.execute("UPDATE questao SET anulada=1 WHERE id_questao BETWEEN 1 AND 20");
            s.execute("UPDATE prova SET status_importacao='RASCUNHO' WHERE id_prova=2");
            s.execute("UPDATE alternativa SET correta=0 WHERE id_questao=41");
            s.execute("UPDATE alternativa SET letra='X' WHERE id_questao=42 AND letra='A'");
        }
        assertEquals(38,repo.acervo().get("questoesAtivas"));
        assertEquals(409,assertThrows(ResponseStatusException.class,()->repo.iniciar(1,hoje)).getStatusCode().value());assertTrue(repo.historico(1).isEmpty());
    }
    @Test void historicoAntigoTambemEvitaRepeticao() throws Exception {
        try(var c=DriverManager.getConnection(url);var s=c.createStatement()) {
            for(int i=1;i<=40;i++)s.execute("INSERT INTO resposta VALUES("+i+",1,TIMESTAMP '2026-11-01 12:00:00')");
        }
        assertTrue(ids(repo.iniciar(1,hoje)).stream().allMatch(id->id>40));
    }
    @Test void concursoAceitaDuasQuatroECincoAlternativasESemanaIsolada() throws Exception {
        var etec=repo.iniciar(1,hoje);
        try(var c=DriverManager.getConnection(url);var s=c.createStatement()) {
            s.execute("INSERT INTO prova VALUES(5,'Concurso','CONCURSO-1','2024','CONCURSO','VALIDADA')");
            s.execute("UPDATE estudante SET objetivo_prova='CONCURSO' WHERE id_estudante=1");
            for(int q=81;q<=140;q++) {
                String letras=q<=100?"CE":q<=120?"ABCD":"ABCDE";
                s.execute("INSERT INTO questao VALUES("+q+",5,"+q+",'Enunciado real',0,'{\"modo\":\"pdf_original\"}')");
                for(int a=0;a<letras.length();a++) s.execute("INSERT INTO alternativa VALUES("+(q*10+a)+","+q+",'"+letras.charAt(a)+"','Resposta',"+(a==0?1:0)+")");
            }
        }
        assertEquals(60,repo.acervo("CONCURSO").get("questoesAtivas"));
        assertEquals(80,repo.acervo().get("questoesAtivas"));
        var concurso=repo.iniciar(1,hoje);long id=((Number)concurso.get("id")).longValue();
        assertEquals("CONCURSO",concurso.get("tipo"));assertNotEquals(etec.get("id"),concurso.get("id"));
        assertTrue(ids(concurso).stream().allMatch(q->q>80));
        for(var q:questoes(concurso)) repo.responder(1,id,q.get("posicao").asInt(),q.get("alternativas").get(0).get("id").asInt());
        assertEquals(40,repo.finalizar(1,id).get("acertos"));
        try(var c=DriverManager.getConnection(url);var s=c.createStatement()){s.execute("UPDATE estudante SET objetivo_prova='ETEC' WHERE id_estudante=1");}
        assertEquals(etec,repo.iniciar(1,hoje));
    }
}
