package br.com.evoluamais.controller;

import br.com.evoluamais.repository.NotificacaoRepository;
import br.com.evoluamais.repository.PushSubscriptionRepository;
import br.com.evoluamais.service.EntregaPushService;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.web.server.ResponseStatusException;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class NotificacaoControllerTest {
    @Test
    void exigeSessaoDoEstudante() {
        NotificacaoController controller=new NotificacaoController(
            mock(NotificacaoRepository.class),mock(PushSubscriptionRepository.class),mock(EntregaPushService.class));
        assertThrows(ResponseStatusException.class,()->controller.listar(new MockHttpSession()));
    }

    @Test
    void naoPermiteEscritaSemCabecalhoDeOrigem() {
        NotificacaoRepository repository=mock(NotificacaoRepository.class);
        NotificacaoController controller=new NotificacaoController(
            repository,mock(PushSubscriptionRepository.class),mock(EntregaPushService.class));
        MockHttpSession session=new MockHttpSession();
        session.setAttribute("idEstudante",42);

        ResponseStatusException erro=assertThrows(ResponseStatusException.class,
            ()->controller.marcarTodasLidas(session,"origem-invalida"));

        assertEquals(403,erro.getStatusCode().value());
        verifyNoInteractions(repository);
    }

    @Test
    void consultaSomenteAsNotificacoesDoEstudanteDaSessao() {
        NotificacaoRepository repository=mock(NotificacaoRepository.class);
        NotificacaoController controller=new NotificacaoController(
            repository,mock(PushSubscriptionRepository.class),mock(EntregaPushService.class));
        MockHttpSession session=new MockHttpSession();
        session.setAttribute("idEstudante",42);

        controller.listar(session);

        verify(repository).listar(42);
    }
}
