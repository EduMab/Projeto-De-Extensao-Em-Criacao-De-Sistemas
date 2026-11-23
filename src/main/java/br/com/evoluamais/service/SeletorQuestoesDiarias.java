package br.com.evoluamais.service;

import java.time.LocalDate;
import java.util.*;

/** Ineditas primeiro; depois o dia de exibicao mais antigo. Equilibra edicoes em cada faixa. */
public final class SeletorQuestoesDiarias {
    public record Candidata(int id, String edicao, LocalDate ultimaExibicao) {}

    public List<Integer> selecionar(List<Candidata> candidatas, int quantidade, Random random) {
        Map<Integer, Candidata> unicas = new LinkedHashMap<>();
        candidatas.forEach(q -> unicas.putIfAbsent(q.id(), q));
        if (unicas.size() < quantidade) throw new IllegalStateException("O acervo ainda nao tem 40 questoes validas.");
        var faixas = new TreeMap<LocalDate, List<Candidata>>(Comparator.nullsFirst(Comparator.naturalOrder()));
        unicas.values().forEach(q -> faixas.computeIfAbsent(q.ultimaExibicao(), k -> new ArrayList<>()).add(q));
        List<Integer> resultado = new ArrayList<>();
        for (var faixa : faixas.values()) {
            Map<String, List<Candidata>> porEdicao = new TreeMap<>();
            faixa.forEach(q -> porEdicao.computeIfAbsent(q.edicao(), k -> new ArrayList<>()).add(q));
            List<Deque<Candidata>> filas = new ArrayList<>();
            for (var grupo : porEdicao.values()) {
                Collections.shuffle(grupo, random);
                filas.add(new ArrayDeque<>(grupo));
            }
            Collections.shuffle(filas, random);
            while (filas.stream().anyMatch(f -> !f.isEmpty())) {
                for (var fila : filas) {
                    if (!fila.isEmpty()) resultado.add(fila.removeFirst().id());
                    if (resultado.size() == quantidade) {
                        Collections.shuffle(resultado, random);
                        return List.copyOf(resultado);
                    }
                }
            }
        }
        throw new IllegalStateException("Acervo insuficiente.");
    }
}
