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
            s.execute("CREATE TABLE estudante(id_estudante INT PRIMARY KEY)");
            s.execute("INSERT INTO estudante VALUES(1),(2)");
            s.execute("CREATE TABLE prova(id_prova INT PRIMARY KEY,nome VARCHAR(100),codigo VARCHAR(160),edicao VARCHAR(80),tipo VARCHAR(20),status_importacao VARCHAR(20))");
            s.execute("CREATE TABLE questao(id_questao INT PRIMARY KEY,id_prova INT,numero_original INT,enunciado CLOB,anulada INT,conteudo_json CLOB)");
            s.execute("CREATE TABLE alternativa(id_alternativa INT PRIMARY KEY,id_questao INT,letra CHAR(1),texto VARCHAR(100),correta INT)");
            s.execute("CREATE TABLE resposta(id_questao INT,id_estudante INT,data_resposta TIMESTAMP)");
            s.execute("CREATE TABLE simulado_diario(id_simulado BIGINT AUTO_INCREMENT PRIMARY KEY,id_estudante INT,tipo VARCHAR(20),data_simulado DATE,concluido_em TIMESTAMP,UNIQUE(id_estudante,data_simulado))");
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

    @Test void mesclaEdicoesRetomaDiaEUsaIneditasAntesDeRepetir() {
        var um=repo.iniciar(1,hoje);var retomado=repo.iniciar(1,hoje);var dois=repo.iniciar(1,hoje.plusDays(1));var tres=repo.iniciar(1,hoje.plusDays(2));
        assertEquals(40,ids(um).size());assertEquals(um,retomado);assertTrue(Collections.disjoint(ids(um),ids(dois)));assertEquals(ids(um),ids(tres));
        assertEquals(4,questoes(um).stream().map(q->q.get("edicao").asText()).distinct().count());
        assertTrue(questoes(um).stream().allMatch(q->!q.has("gabarito")&&!q.has("acertou")));assertFalse(um.containsKey("acertos"));
        assertEquals(3,repo.historico(1).size());assertTrue(repo.historico(2).isEmpty());
    }
    @Test void chamadasSimultaneasRecebemAMesmaSelecao() throws Exception {
        try(var executor=Executors.newVirtualThreadPerTaskExecutor()) {
            var gate=new CountDownLatch(1);
            var a=executor.submit(()->{gate.await();return repo.iniciar(1,hoje);});
            var b=executor.submit(()->{gate.await();return repo.iniciar(1,hoje);});gate.countDown();
            assertEquals(a.get(20,TimeUnit.SECONDS),b.get(20,TimeUnit.SECONDS));assertEquals(1,repo.historico(1).size());
        }
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
}
