package br.com.evoluamais.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class UsuarioController {

    @GetMapping("/usuarios/teste")
    public String teste() {
        return "UsuarioController funcionando!";
    }
}