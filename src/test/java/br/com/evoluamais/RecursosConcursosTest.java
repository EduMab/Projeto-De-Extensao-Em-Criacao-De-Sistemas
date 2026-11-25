package br.com.evoluamais;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.zip.GZIPInputStream;
import static org.junit.jupiter.api.Assertions.*;

class RecursosConcursosTest {
    @Test void todosOsRecortesEstaoNosRecursosPublicados() throws Exception {
        var paths = new HashSet<String>();
        try (var input = new GZIPInputStream(Files.newInputStream(Path.of("acervo/concursos/questoes-recortadas.json.gz")))) {
            var data = new ObjectMapper().readTree(input);
            for (var prova : data.path("provas")) {
                paths.add("/questoes/concursos/pci-" + prova.path("slug").asText() + "/prova.pdf");
                for (var questao : prova.path("questoes"))
                    for (var recorte : questao.path("conteudo").path("recortes"))
                        paths.add(recorte.path("imagem").asText());
            }
        }
        assertTrue(paths.size() >= 374);
        for (String path : paths) {
            try (InputStream asset = getClass().getResourceAsStream("/static" + path)) {
                assertNotNull(asset, "Recurso ausente no build: " + path);
                String header = new String(asset.readNBytes(12), StandardCharsets.ISO_8859_1);
                if (path.endsWith(".webp")) {
                    assertTrue(header.startsWith("RIFF"), path);
                    assertEquals("WEBP", header.substring(8, 12), path);
                } else assertTrue(header.startsWith("%PDF-"), path);
            }
        }
    }
}
