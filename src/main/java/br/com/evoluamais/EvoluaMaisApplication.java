package br.com.evoluamais;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class EvoluaMaisApplication {

    public static void main(String[] args) {
        SpringApplication.run(EvoluaMaisApplication.class, args);
    }
}