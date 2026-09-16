# 🤖📚 Projeto: Plano de Estudos com IA

Olá, Seja muito Bem-vindo(a) ao nosso projeto! Nossa proposta é um assistente de planejamento de estudos personalizado, desenvolvido com Inteligência Artificial para auxiliar estudantes na organização de sua rotina e no alcance de seus objetivos.

#  Sobre o Projeto:

A plataforma consiste em um assistente de planejamento de estudos personalizado, desenvolvido com IA para auxiliar estudantes na preparação para vestibulares, concursos públicos ou outros objetivos. 

Alinhada à ODS 4 — Educação de Qualidade, a solução busca democratizar o acesso à orientação de estudos, enfrentando problemas como falta de direcionamento, dificuldade na organização do tempo e cronogramas pouco realistas, que podem levar à desmotivação e à desistência.

A Inteligência Artificial é o principal diferencial da nossa plataforma, utilizando um modelo integrado por API para analisar os objetivos, disponibilidade, prazos e progresso de cada usuário. A partir desses dados, a IA gera cronogramas personalizados, recomenda prioridades, produz resumos de conteúdos, tornando a orientação de estudos mais acessível, prática e adaptativa, especialmente para estudantes que não possuem condições de investir em mentorias ou cursinhos.



## 🧩 Diagrama de Classes:


```mermaid
classDiagram

class Aluno {
    -int id
    -String nome
    -String email
    -String senha
    +cadastrar()
    +atualizarPerfil()
    +visualizarPlano()
}

class ObjetivoEstudo {
    -int id
    -String descricao
    -Date dataLimite
    -String prioridade
    +definirObjetivo()
    +atualizarPrazo()
}

class Disciplina {
    -int id
    -String nome
    -String dificuldade
    +adicionarConteudo()
}

class Conteudo {
    -int id
    -String titulo
    -String dificuldade
    -String status
    +marcarConcluido()
}

class PlanoEstudos {
    -int id
    -Date dataCriacao
    -Date dataInicio
    -Date dataFim
    -String status
    +atualizarPlano()
}

class AssistenteIA {
    +gerarPlano()
    +reorganizarPlano()
    +sugerirPrioridades()
}

Aluno  -->  ObjetivoEstudo
Aluno  -->  Disciplina
Aluno  -->  PlanoEstudos
Disciplina  -->  Conteudo
AssistenteIA --> PlanoEstudos
```

<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net"><diagram name="Página-1" id="hJj1Xf6WvSrlDZ4Yw0q9">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</diagram></mxfile>
