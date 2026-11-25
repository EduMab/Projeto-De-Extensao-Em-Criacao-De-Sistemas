package br.com.evoluamais.controller;

import br.com.evoluamais.repository.NotificacaoRepository;
import br.com.evoluamais.repository.PushSubscriptionRepository;
import br.com.evoluamais.service.EntregaPushService;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.net.URI;
import java.util.Base64;
import java.util.Map;

@RestController
@RequestMapping("/api/notificacoes")
public class NotificacaoController {
    private final NotificacaoRepository repository;
    private final PushSubscriptionRepository assinaturas;
    private final EntregaPushService push;

    public NotificacaoController(NotificacaoRepository repository,
            PushSubscriptionRepository assinaturas, EntregaPushService push) {
        this.repository=repository; this.assinaturas=assinaturas; this.push=push;
    }

    private int estudante(HttpSession session) {
        Object id=session.getAttribute("idEstudante");
        if(!(id instanceof Integer))
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED,"Faça login para acessar suas notificações.");
        return (Integer)id;
    }

    private void validarOrigem(String origem) {
        if(!"notificacoes".equals(origem))
            throw new ResponseStatusException(HttpStatus.FORBIDDEN,"Requisição inválida.");
    }

    @GetMapping
    public Map<String,Object> listar(HttpSession session) { return repository.listar(estudante(session)); }

    @PostMapping("/{id}/lida")
    public Map<String,Boolean> marcarLida(@PathVariable long id,HttpSession session,
            @RequestHeader(value="X-Evolua-Request",required=false) String origem) {
        estudante(session); validarOrigem(origem);
        repository.marcarLida(estudante(session),id);
        return Map.of("sucesso",true);
    }

    @PostMapping("/lidas")
    public Map<String,Boolean> marcarTodasLidas(HttpSession session,
            @RequestHeader(value="X-Evolua-Request",required=false) String origem) {
        int id=estudante(session); validarOrigem(origem);
        repository.marcarTodasLidas(id);
        return Map.of("sucesso",true);
    }

    @GetMapping("/push/config")
    public Map<String,Object> configuracaoPush(HttpSession session) {
        estudante(session);
        return Map.of("ativo",push.ativo(),"chavePublica",push.ativo()?push.chavePublica():"");
    }

    public record Chaves(String p256dh,String auth) {}
    public record AssinaturaRequest(String endpoint,Chaves keys) {}

    @PostMapping("/push/assinatura")
    public Map<String,Boolean> inscrever(@RequestBody AssinaturaRequest request,HttpSession session,
            @RequestHeader(value="X-Evolua-Request",required=false) String origem) {
        int id=estudante(session); validarOrigem(origem);
        if(!push.ativo()) throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Avisos no dispositivo ainda não estão configurados.");
        if(request==null||request.keys()==null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Assinatura inválida.");
        validarEndpoint(request.endpoint());
        validarChave(request.keys().p256dh(),65,"Chave pública");
        validarChave(request.keys().auth(),16,"Chave de autenticação");
        assinaturas.salvar(id,request.endpoint(),request.keys().p256dh(),request.keys().auth());
        return Map.of("sucesso",true);
    }

    @DeleteMapping("/push/assinatura")
    public Map<String,Boolean> desinscrever(@RequestBody Map<String,String> body,HttpSession session,
            @RequestHeader(value="X-Evolua-Request",required=false) String origem) {
        int id=estudante(session); validarOrigem(origem);
        String endpoint=body==null?null:body.get("endpoint");
        validarEndpoint(endpoint);
        assinaturas.remover(id,endpoint);
        return Map.of("sucesso",true);
    }

    private void validarChave(String valor,int tamanho,String nome) {
        try {
            if(valor==null||Base64.getUrlDecoder().decode(valor).length!=tamanho)
                throw new IllegalArgumentException();
        } catch(Exception e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,nome+" inválida.");
        }
    }

    /** Restringe endpoints aos servicos conhecidos de push dos navegadores (mitigacao SSRF). */
    private void validarEndpoint(String endpoint) {
        try {
            if(endpoint==null||endpoint.length()>2048) throw new IllegalArgumentException();
            URI uri=URI.create(endpoint);
            String host=uri.getHost();
            boolean hostValido=host!=null && (
                host.equals("fcm.googleapis.com") ||
                host.equals("web.push.apple.com") ||
                host.equals("updates.push.services.mozilla.com") ||
                host.endsWith(".push.services.mozilla.com") ||
                host.endsWith(".notify.windows.com"));
            if(!"https".equalsIgnoreCase(uri.getScheme())||!hostValido||
                    (uri.getPort()!=-1&&uri.getPort()!=443)||uri.getUserInfo()!=null||uri.getFragment()!=null)
                throw new IllegalArgumentException();
        } catch(Exception e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Endereço de notificação do navegador inválido.");
        }
    }
}
