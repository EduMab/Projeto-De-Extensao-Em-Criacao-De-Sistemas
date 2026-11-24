package br.com.evoluamais.service;

import br.com.evoluamais.repository.NotificacaoRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.ZoneId;

@Component
public class NotificacaoSemanalAgendador {
    private static final Logger log=LoggerFactory.getLogger(NotificacaoSemanalAgendador.class);
    private static final ZoneId FUSO=ZoneId.of("America/Sao_Paulo");
    private final NotificacaoRepository repository;
    private final EntregaPushService push;

    public NotificacaoSemanalAgendador(NotificacaoRepository repository, EntregaPushService push) {
        this.repository=repository; this.push=push;
    }

    /** Faz uma verificacao assim que a aplicacao fica pronta, util apos reinicios do host. */
    @EventListener(ApplicationReadyEvent.class)
    public void verificarAoIniciar() { verificarTarefas(); }

    /** Roda diariamente as 9h: cria avisos do ciclo semanal e tenta entrega push. */
    @Scheduled(cron="0 0 9 * * *",zone="America/Sao_Paulo")
    public void verificarTarefas() {
        try {
            int criadas=repository.gerarPendentes(LocalDate.now(FUSO));
            int enviadas=push.enviarPendentes();
            if(criadas>0||enviadas>0)
                log.info("Notificacoes semanais: {} criadas; {} enviadas por push.",criadas,enviadas);
        } catch(Exception e) {
            log.error("Falha ao processar notificacoes semanais.",e);
        }
    }
}
