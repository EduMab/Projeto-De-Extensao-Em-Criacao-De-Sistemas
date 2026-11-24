package br.com.evoluamais.service;

import br.com.evoluamais.repository.NotificacaoRepository;
import br.com.evoluamais.repository.PushSubscriptionRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import nl.martijndwars.webpush.Notification;
import nl.martijndwars.webpush.PushService;
import org.apache.http.HttpResponse;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.security.Security;
import java.util.*;

@Service
public class EntregaPushService {
    private static final Logger log=LoggerFactory.getLogger(EntregaPushService.class);
    private final NotificacaoRepository notificacoes;
    private final PushSubscriptionRepository assinaturas;
    private final ObjectMapper mapper=new ObjectMapper();
    private final PushService pushService;
    private final boolean ativo;

    public EntregaPushService(NotificacaoRepository notificacoes, PushSubscriptionRepository assinaturas) {
        this.notificacoes=notificacoes;
        this.assinaturas=assinaturas;
        String publica=System.getenv("VAPID_PUBLIC_KEY");
        String privada=System.getenv("VAPID_PRIVATE_KEY");
        String assunto=System.getenv("VAPID_SUBJECT");
        PushService service=null;
        boolean configurado=publica!=null&&!publica.isBlank()&&privada!=null&&!privada.isBlank()
                &&assunto!=null&&!assunto.isBlank();
        if(configurado) {
            try {
                if(Security.getProvider(BouncyCastleProvider.PROVIDER_NAME)==null)
                    Security.addProvider(new BouncyCastleProvider());
                service=new PushService(publica,privada,assunto);
            } catch(Exception e) {
                log.error("Configuracao VAPID invalida; notificacoes no painel continuam funcionando.",e);
                configurado=false;
            }
        }
        this.pushService=service;
        this.ativo=configurado;
        if(!ativo) log.warn("Web Push desativado: configure VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY e VAPID_SUBJECT.");
    }

    public boolean ativo(){return ativo;}
    public String chavePublica(){return ativo?System.getenv("VAPID_PUBLIC_KEY"):null;}

    /** Envia a fila pendente. Uma notificacao so e marcada como entregue apos resposta 2xx. */
    public int enviarPendentes() {
        if(!ativo) return 0;
        List<NotificacaoRepository.EntregaPush> fila=notificacoes.buscarEntregasPushPendentes();
        Map<Long,List<NotificacaoRepository.EntregaPush>> porNotificacao=new LinkedHashMap<>();
        for(var entrega:fila) porNotificacao.computeIfAbsent(entrega.idNotificacao(),k->new ArrayList<>()).add(entrega);
        int entregues=0;
        for(var grupo:porNotificacao.entrySet()) {
            boolean sucesso=false;
            for(var entrega:grupo.getValue()) {
                try {
                    String payload=mapper.writeValueAsString(Map.of(
                        "title",entrega.titulo(),"body",entrega.mensagem(),
                        "url",entrega.link(),"tag","evolua-notificacao-"+entrega.idNotificacao()));
                    Notification notification=new Notification(entrega.endpoint(),entrega.p256dh(),
                        entrega.auth(),payload,3600);
                    HttpResponse response=pushService.send(notification);
                    int status=response.getStatusLine().getStatusCode();
                    if(status>=200&&status<300) sucesso=true;
                    else if(status==404||status==410) assinaturas.removerEndpoint(entrega.endpoint());
                    else log.warn("Push retornou HTTP {} para notificacao {}",status,entrega.idNotificacao());
                } catch(Exception e) {
                    log.warn("Falha temporaria no push da notificacao {}: {}",entrega.idNotificacao(),e.getMessage());
                }
            }
            if(sucesso) {
                notificacoes.marcarPushEnviado(grupo.getKey());
                entregues++;
            } else {
                notificacoes.registrarFalhaPush(grupo.getKey(),"Nenhum dispositivo confirmou a entrega.");
            }
        }
        return entregues;
    }
}
