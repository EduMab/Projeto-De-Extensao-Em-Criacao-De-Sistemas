package br.com.evoluamais.service;

import br.com.evoluamais.repository.NotificacaoRepository;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class NotificacaoSemanalAgendadorTest {
    @Test
    void processaGeracaoDeAvisosEEntregaPush() {
        NotificacaoRepository repository=mock(NotificacaoRepository.class);
        EntregaPushService push=mock(EntregaPushService.class);
        when(repository.gerarPendentes(any(LocalDate.class))).thenReturn(2);
        when(push.enviarPendentes()).thenReturn(1);

        NotificacaoSemanalAgendador agendador=new NotificacaoSemanalAgendador(repository,push);
        agendador.verificarTarefas();

        verify(repository,times(1)).gerarPendentes(any(LocalDate.class));
        verify(push,times(1)).enviarPendentes();
    }

    @Test
    void naoInterrompeAgendadorQuandoBancoFalha() {
        NotificacaoRepository repository=mock(NotificacaoRepository.class);
        EntregaPushService push=mock(EntregaPushService.class);
        when(repository.gerarPendentes(any(LocalDate.class))).thenThrow(new IllegalStateException("Banco indisponível"));

        NotificacaoSemanalAgendador agendador=new NotificacaoSemanalAgendador(repository,push);
        agendador.verificarTarefas();

        verify(push,never()).enviarPendentes();
    }
}
