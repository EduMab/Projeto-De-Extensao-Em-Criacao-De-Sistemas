package br.com.evoluamais.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Apresentação dos snapshots ETEC, mantendo no banco os originais e as respostas. */
public final class ApresentacaoEtec {
    private static final JsonNode RECORTES = carregar();
    private ApresentacaoEtec() {}

    private static JsonNode carregar() {
        try (var source = ApresentacaoEtec.class.getResourceAsStream("/etec-recortes.json.gz")) {
            if (source == null) throw new IllegalStateException("Índice de recortes ETEC ausente");
            return new ObjectMapper().readTree(new java.util.zip.GZIPInputStream(source));
        } catch (Exception e) { throw new IllegalStateException("Índice de recortes ETEC inválido", e); }
    }

    public static void aplicar(ObjectNode questao) {
        JsonNode conteudo = questao.path("conteudo");
        if (!"pagina_original".equals(conteudo.path("modo").asText())) return;
        JsonNode recorte = RECORTES.path(questao.path("edicao").asText() + "/" + questao.path("numeroOriginal").asInt());
        // A coordenada do título liga o índice à mesma versão do caderno do snapshot.
        if (recorte.isMissingNode() || !recorte.path("caixaTitulo").equals(conteudo.path("caixaTitulo"))
                || recorte.path("pagina").asInt() != conteudo.path("pagina").asInt()) return;
        ObjectNode exibicao = ((ObjectNode) conteudo).deepCopy();
        exibicao.put("modo", "recorte_original");
        exibicao.set("recortes", recorte.path("recortes").deepCopy());
        exibicao.remove(java.util.List.of("paginas", "apoioAnterior", "caixaTitulo"));
        questao.set("conteudo", exibicao);
    }
}
