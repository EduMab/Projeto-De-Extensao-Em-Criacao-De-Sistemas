package br.com.evoluamais.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

class ApresentacaoEtecTest {
    private final ObjectMapper mapper = new ObjectMapper();

    @Test void converteTodoOAcervoSemModificarSnapshotOrigemOuGabarito() throws Exception {
        var data = mapper.readTree(Path.of("acervo/etec/questoes.json").toFile());
        int total=0;
        for (var edicao : data.path("edicoes")) for (var item : edicao.path("questoes")) {
            ObjectNode original = mapper.createObjectNode();
            original.put("edicao", edicao.path("edicao").asText());
            original.put("numeroOriginal", item.path("numero").asInt());
            original.put("alternativaSelecionada", 123);
            original.set("gabarito", item.path("gabarito"));
            original.set("conteudo", item.path("conteudo").deepCopy());
            var saved = original.deepCopy(); var response=original.deepCopy();
            ApresentacaoEtec.aplicar(response);
            assertEquals(saved, original);
            assertEquals("recorte_original", response.path("conteudo").path("modo").asText());
            assertFalse(response.path("conteudo").has("paginas"));
            assertFalse(response.path("conteudo").has("apoioAnterior"));
            assertEquals(saved.path("gabarito"), response.path("gabarito"));
            assertEquals(123, response.path("alternativaSelecionada").asInt());
            assertTrue(response.path("conteudo").path("recortes").findValuesAsText("tipo").contains("questao"));
            total++;
        }
        assertEquals(790,total);
    }

    @Test void tituloDivergenteOuOutroFormatoNaoRecebeRecorteDeOutraVersao() throws Exception {
        ObjectNode q=(ObjectNode)mapper.readTree("{\"edicao\":\"2026-2\",\"numeroOriginal\":32,\"conteudo\":{\"modo\":\"pagina_original\",\"pagina\":15,\"caixaTitulo\":[0,0,1,1]}}");
        var original=q.deepCopy();ApresentacaoEtec.aplicar(q);assertEquals(original,q);
        ((ObjectNode)q.path("conteudo")).put("modo","recorte_original");
        original=q.deepCopy();ApresentacaoEtec.aplicar(q);assertEquals(original,q);
    }
}
