package br.com.evoluamais.service;

import br.com.evoluamais.repository.NotificacaoRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.ZoneId;

@Component
public class NotificacaoSemanalAgendador {
    private static final Logger log = LoggerFactory.getLogger(NotificacaoSemanalAgendador.class);
    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");
    private final NotificacaoRepository repository;

    public NotificacaoSemanalAgendador(NotificacaoRepository repository) {
        this.repository = repository;
    }

    /** Verifica diariamente às 9h se há tarefa nova ou simulado pendente. */
    @Scheduled(cron = "0 0 9 * * *", zone = "America/Sao_Paulo")
    public void verificarTarefas() {
        try {
            int total = repository.gerarPendentes(LocalDate.now(FUSO));
            if (total > 0) log.info("Notificações semanais criadas: {}", total);
        } catch (Exception e) {
            log.error("Falha ao verificar notificações semanais.", e);
        }
    }
}
