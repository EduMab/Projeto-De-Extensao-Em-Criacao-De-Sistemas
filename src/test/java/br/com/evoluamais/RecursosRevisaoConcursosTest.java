package br.com.evoluamais;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

class RecursosRevisaoConcursosTest {
    @Test void buildComRevisaoContemAs395ImagensAprovadas() throws Exception {
        assumeTrue(Files.exists(Path.of("acervo/concursos/recortes-revisao-enem.zip")), "Recursos revisados são gerados no build Docker.");
        var imagens=new ObjectMapper().readTree(Files.readString(Path.of("acervo/concursos-previa-enem/aprovacao.json"))).path("imagens");
        assertEquals(395,imagens.size());
        for(var it=imagens.fields();it.hasNext();) {
            var image=it.next();
            try(var asset=getClass().getResourceAsStream("/static"+image.getKey())) {
                assertNotNull(asset,image.getKey());
                var digest=MessageDigest.getInstance("SHA-256").digest(asset.readAllBytes());
                assertEquals(image.getValue().asText(),HexFormat.of().formatHex(digest),image.getKey());
            }
        }
    }
}
