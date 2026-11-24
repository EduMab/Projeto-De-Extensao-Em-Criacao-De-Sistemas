package br.com.evoluamais.config;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.HandlerMapping;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Aplica a mesma propriedade de sessao do simulado semanal as rotas do MVP. */
@Configuration
public class AcessoEstudanteConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new AcessoEstudante())
                .addPathPatterns("/ia/**", "/respostas/**", "/simulado/**");
    }

    private static final class AcessoEstudante implements HandlerInterceptor {
        @Override
        public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
            var session = request.getSession(false);
            Object id = session == null ? null : session.getAttribute("idEstudante");
            if (!(id instanceof Integer estudante)) {
                throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Faca login para acessar seus dados.");
            }

            List<String> alvos = new ArrayList<>();
            Object variaveis = request.getAttribute(HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE);
            if (variaveis instanceof Map<?, ?> mapa && mapa.get("idEstudante") != null) {
                alvos.add(mapa.get("idEstudante").toString());
            }
            String[] parametros = request.getParameterValues("idEstudante");
            if (parametros != null) alvos.addAll(List.of(parametros));
            if (alvos.isEmpty()) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Informe o estudante.");
            }
            for (String alvo : alvos) {
                int solicitado;
                try { solicitado = Integer.parseInt(alvo); }
                catch (NumberFormatException e) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Estudante invalido.");
                }
                if (solicitado != estudante) {
                    throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Acesse apenas os dados da sua conta.");
                }
            }
            return true;
        }
    }
}
