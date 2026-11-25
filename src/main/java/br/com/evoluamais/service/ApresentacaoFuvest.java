package br.com.evoluamais.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Apresenta a questão individual sem alterar snapshots, respostas ou gabaritos. */
public final class ApresentacaoFuvest {
    private static final JsonNode RECORTES = carregar();
    private ApresentacaoFuvest() {}

    private static JsonNode carregar() {
        try (var source = ApresentacaoFuvest.class.getResourceAsStream("/fuvest-recortes.json.gz")) {
            if (source == null) throw new IllegalStateException("Índice de recortes FUVEST ausente");
            return new ObjectMapper().readTree(new java.util.zip.GZIPInputStream(source));
        } catch (Exception e) { throw new IllegalStateException("Índice de recortes FUVEST inválido", e); }
    }

    public static void aplicar(ObjectNode questao) {
        JsonNode conteudo = questao.path("conteudo");
        if (!"pagina_original".equals(conteudo.path("modo").asText())) return;
        JsonNode recorte = RECORTES.path(questao.path("edicao").asText() + "/" + questao.path("numeroOriginal").asInt());
        // Título, página e URL vinculam o recorte ao mesmo caderno do snapshot.
        if (recorte.isMissingNode() || !recorte.path("caixaTitulo").equals(conteudo.path("caixaTitulo"))
                || !recorte.path("pagina").equals(conteudo.path("pagina"))
                || !recorte.path("urlProva").equals(conteudo.path("urlProva"))) return;
        ObjectNode exibicao = ((ObjectNode) conteudo).deepCopy();
        exibicao.put("modo", "recorte_original");
        exibicao.set("recortes", recorte.path("recortes").deepCopy());
        exibicao.remove(java.util.List.of("paginas", "apoioAnterior", "caixaTitulo"));
        questao.set("conteudo", exibicao);
    }
}
