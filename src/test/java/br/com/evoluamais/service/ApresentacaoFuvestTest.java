package br.com.evoluamais.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.zip.GZIPInputStream;
import static org.junit.jupiter.api.Assertions.*;

class ApresentacaoFuvestTest {
    private final ObjectMapper mapper = new ObjectMapper();

    @Test void apresentaAs890QuestoesPreservandoRespostasEOriginais() throws Exception {
        try (var source = new GZIPInputStream(Files.newInputStream(Path.of("acervo/fuvest/questoes.json.gz")))) {
            var acervo = mapper.readTree(source);
            int total = 0;
            for (var edicao : acervo.path("edicoes")) for (var item : edicao.path("questoes")) {
                ObjectNode original = mapper.createObjectNode();
                original.put("edicao", edicao.path("ano").asText());
                original.put("numeroOriginal", item.path("numero").asInt());
                original.put("alternativaSelecionada", 123);
                original.put("acertou", true);
                original.set("gabarito", item.path("gabarito"));
                original.set("conteudo", item.path("conteudo").deepCopy());
                var saved = original.deepCopy();
                var response = original.deepCopy();
                ApresentacaoFuvest.aplicar(response);
                assertEquals(saved, original);
                var c = response.path("conteudo");
                assertEquals("recorte_original", c.path("modo").asText());
                assertFalse(c.has("paginas"));
                assertFalse(c.has("apoioAnterior"));
                assertEquals(1, c.path("recortes").size());
                assertEquals("questao", c.path("recortes").get(0).path("tipo").asText());
                assertEquals(saved.path("gabarito"), response.path("gabarito"));
                assertEquals(123, response.path("alternativaSelecionada").asInt());
                assertTrue(response.path("acertou").asBoolean());
                total++;
            }
            assertEquals(890, total);
        }
    }

    @Test void naoAplicaRecorteDeOutroCadernoOuVersao() throws Exception {
        var indice = mapper.readTree(new GZIPInputStream(getClass().getResourceAsStream("/fuvest-recortes.json.gz")));
        ObjectNode q = mapper.createObjectNode();
        q.put("edicao", "2027"); q.put("numeroOriginal", 1);
        ObjectNode conteudo = (ObjectNode) indice.path("2027/1").deepCopy();
        conteudo.put("modo", "pagina_original"); q.set("conteudo", conteudo);
        for (String campo : java.util.List.of("caixaTitulo", "pagina", "urlProva")) {
            var diferente = q.deepCopy();
            ((ObjectNode) diferente.path("conteudo")).remove(campo);
            var antes = diferente.deepCopy();
            ApresentacaoFuvest.aplicar(diferente);
            assertEquals(antes, diferente);
        }
        conteudo.put("modo", "recorte_original");
        var antes = q.deepCopy(); ApresentacaoFuvest.aplicar(q); assertEquals(antes, q);
    }
}
