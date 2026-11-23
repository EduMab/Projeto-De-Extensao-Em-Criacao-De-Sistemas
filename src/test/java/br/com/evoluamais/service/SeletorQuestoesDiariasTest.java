package br.com.evoluamais.service;
import org.junit.jupiter.api.Test;
import java.time.LocalDate;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SeletorQuestoesDiariasTest {
    @Test void acervo787Entrega19DiasSemRepetirEDepois27Ineditas() {
        var seletor=new SeletorQuestoesDiarias();var random=new Random(17);var ultima=new HashMap<Integer,LocalDate>();var vistos=new HashSet<Integer>();
        for(int dia=0;dia<20;dia++) {
            var candidatas=new ArrayList<SeletorQuestoesDiarias.Candidata>();
            for(int i=1;i<=787;i++)candidatas.add(new SeletorQuestoesDiarias.Candidata(i,"Edicao-"+(i%16),ultima.get(i)));
            var selecionadas=seletor.selecionar(candidatas,40,random);assertEquals(40,new HashSet<>(selecionadas).size());
            int novas=(int)selecionadas.stream().filter(id->!vistos.contains(id)).count();assertEquals(dia<19?40:27,novas);
            var data=LocalDate.of(2026,1,1).plusDays(dia);selecionadas.forEach(id->{vistos.add(id);ultima.put(id,data);});
        }
        assertEquals(787,vistos.size());
    }
}
