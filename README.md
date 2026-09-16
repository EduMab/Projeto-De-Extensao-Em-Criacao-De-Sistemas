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
<mxfile host="app.diagrams.net">
  <diagram name="Página-1" id="Fx5YuHXEn6CJSMVBnzI0">
    <mxGraphModel dx="2060" dy="1124" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <object placeholders="1" c4Name="Aluno" c4Type="Person" c4Description="Usuário da plataforma de ensino" label="&lt;font style=&quot;font-size: 16px&quot;&gt;&lt;b&gt;%c4Name%&lt;/b&gt;&lt;/font&gt;&lt;div&gt;[%c4Type%]&lt;/div&gt;&lt;br&gt;&lt;div&gt;&lt;font style=&quot;font-size: 11px&quot;&gt;&lt;font color=&quot;#cccccc&quot;&gt;%c4Description%&lt;/font&gt;&lt;/div&gt;" id="N1oVapyl2h7FQJmYYXLb-1">
          <mxCell parent="1" style="html=1;fontSize=11;dashed=0;whiteSpace=wrap;fillColor=#083F75;strokeColor=#06315C;fontColor=#ffffff;shape=mxgraph.c4.person2;align=center;metaEdit=1;points=[[0.5,0,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0]];resizable=0;" vertex="1">
            <mxGeometry height="180" width="200" x="100" y="40" as="geometry" />
          </mxCell>
        </object>
        <object placeholders="1" c4Name="Administrador " c4Type="Person" c4Description="Responsável por gerenciar desenvolvimento do site&#xa;" label="&lt;font style=&quot;font-size: 16px&quot;&gt;&lt;b&gt;%c4Name%&lt;/b&gt;&lt;/font&gt;&lt;div&gt;[%c4Type%]&lt;/div&gt;&lt;br&gt;&lt;div&gt;&lt;font style=&quot;font-size: 11px&quot;&gt;&lt;font color=&quot;#cccccc&quot;&gt;%c4Description%&lt;/font&gt;&lt;/div&gt;" id="N1oVapyl2h7FQJmYYXLb-3">
          <mxCell parent="1" style="html=1;fontSize=11;dashed=0;whiteSpace=wrap;fillColor=#083F75;strokeColor=#06315C;fontColor=#ffffff;shape=mxgraph.c4.person2;align=center;metaEdit=1;points=[[0.5,0,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0]];resizable=0;" vertex="1">
            <mxGeometry height="180" width="200" x="540" y="50" as="geometry" />
          </mxCell>
        </object>
        <object placeholders="1" c4Name="Evolua+" c4Type="Software System" c4Description="Plataforma de ensino integrado a IA" label="&lt;font style=&quot;font-size: 16px&quot;&gt;&lt;b&gt;%c4Name%&lt;/b&gt;&lt;/font&gt;&lt;div&gt;[%c4Type%]&lt;/div&gt;&lt;br&gt;&lt;div&gt;&lt;font style=&quot;font-size: 11px&quot;&gt;&lt;font color=&quot;#cccccc&quot;&gt;%c4Description%&lt;/font&gt;&lt;/div&gt;" id="N1oVapyl2h7FQJmYYXLb-4">
          <mxCell parent="1" style="rounded=1;whiteSpace=wrap;html=1;labelBackgroundColor=none;fillColor=#1061B0;fontColor=#ffffff;align=center;arcSize=10;strokeColor=#0D5091;metaEdit=1;resizable=0;points=[[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];" vertex="1">
            <mxGeometry height="120" width="240" x="300" y="340" as="geometry" />
          </mxCell>
        </object>
        <object placeholders="1" c4Name="Inteligência Artificial " c4Type="Software System" c4Description="Gerenciamento de plano de estudo" label="&lt;font style=&quot;font-size: 16px&quot;&gt;&lt;b&gt;%c4Name%&lt;/b&gt;&lt;/font&gt;&lt;div&gt;[%c4Type%]&lt;/div&gt;&lt;br&gt;&lt;div&gt;&lt;font style=&quot;font-size: 11px&quot;&gt;&lt;font color=&quot;#cccccc&quot;&gt;%c4Description%&lt;/font&gt;&lt;/div&gt;" id="N1oVapyl2h7FQJmYYXLb-5">
          <mxCell parent="1" style="rounded=1;whiteSpace=wrap;html=1;labelBackgroundColor=none;fillColor=#8C8496;fontColor=#ffffff;align=center;arcSize=10;strokeColor=#736782;metaEdit=1;resizable=0;points=[[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];" vertex="1">
            <mxGeometry height="120" width="240" x="60" y="550" as="geometry" />
          </mxCell>
        </object>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-23" edge="1" parent="1" source="N1oVapyl2h7FQJmYYXLb-6" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.75;exitY=0;exitDx=0;exitDy=0;exitPerimeter=0;entryX=1.001;entryY=0.832;entryDx=0;entryDy=0;entryPerimeter=0;" target="N1oVapyl2h7FQJmYYXLb-4">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="719.6666666666667" y="480" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-24" connectable="0" parent="N1oVapyl2h7FQJmYYXLb-23" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" value="Retorna relatório&amp;nbsp;" vertex="1">
          <mxGeometry relative="1" x="0.2796" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
        <object placeholders="1" c4Name="Banco de dados " c4Type="Software System" c4Description="Fazer levantamento de dados pra acompanhar desenvolvimento de ensino&#xa; " label="&lt;font style=&quot;font-size: 16px&quot;&gt;&lt;b&gt;%c4Name%&lt;/b&gt;&lt;/font&gt;&lt;div&gt;[%c4Type%]&lt;/div&gt;&lt;br&gt;&lt;div&gt;&lt;font style=&quot;font-size: 11px&quot;&gt;&lt;font color=&quot;#cccccc&quot;&gt;%c4Description%&lt;/font&gt;&lt;/div&gt;" id="N1oVapyl2h7FQJmYYXLb-6">
          <mxCell parent="1" style="rounded=1;whiteSpace=wrap;html=1;labelBackgroundColor=none;fillColor=#8C8496;fontColor=#ffffff;align=center;arcSize=10;strokeColor=#736782;metaEdit=1;resizable=0;points=[[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];" vertex="1">
            <mxGeometry height="120" width="240" x="540" y="560" as="geometry" />
          </mxCell>
        </object>
        <object placeholders="1" c4Name="[System Context]Evolua+" c4Type="ContainerScopeBoundary" c4Description="Visão Geral&#xa;Ultima atualização:&#xa;14/09/2026" label="&lt;font style=&quot;font-size: 16px&quot;&gt;&lt;b&gt;&lt;div style=&quot;text-align: left&quot;&gt;%c4Name%&lt;/div&gt;&lt;/b&gt;&lt;/font&gt;&lt;div style=&quot;text-align: left&quot;&gt;%c4Description%&lt;/div&gt;" id="N1oVapyl2h7FQJmYYXLb-7">
          <mxCell parent="1" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;metaEdit=1;allowArrows=0;resizable=1;rotatable=0;connectable=0;recursiveResize=0;expand=0;pointerEvents=0;points=[[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];" vertex="1">
            <mxGeometry height="40" width="260" x="30" y="1060" as="geometry" />
          </mxCell>
        </object>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-8" edge="1" parent="1" source="N1oVapyl2h7FQJmYYXLb-1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.75;exitY=1;exitDx=0;exitDy=0;exitPerimeter=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;entryPerimeter=0;" target="N1oVapyl2h7FQJmYYXLb-4">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-9" connectable="0" parent="N1oVapyl2h7FQJmYYXLb-8" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" value="&lt;div&gt;&lt;br&gt;&lt;/div&gt;Acessa plataforma para estudos&amp;nbsp;&lt;div&gt;Cadastro&lt;/div&gt;&lt;div&gt;&lt;br&gt;&lt;/div&gt;" vertex="1">
          <mxGeometry relative="1" x="-0.3797" y="2" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-13" edge="1" parent="1" source="N1oVapyl2h7FQJmYYXLb-3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.25;exitY=1;exitDx=0;exitDy=0;exitPerimeter=0;entryX=1;entryY=0.25;entryDx=0;entryDy=0;entryPerimeter=0;" target="N1oVapyl2h7FQJmYYXLb-4">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-14" connectable="0" parent="N1oVapyl2h7FQJmYYXLb-13" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" value="Acessa plataforma para gerenciar&amp;nbsp;" vertex="1">
          <mxGeometry relative="1" x="-0.3193" y="-2" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-15" edge="1" parent="1" source="N1oVapyl2h7FQJmYYXLb-4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;exitPerimeter=0;entryX=0.457;entryY=0.017;entryDx=0;entryDy=0;entryPerimeter=0;" target="N1oVapyl2h7FQJmYYXLb-5">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="420" y="500" />
              <mxPoint x="169.72" y="500" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-19" connectable="0" parent="N1oVapyl2h7FQJmYYXLb-15" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" value="Levantamento de informações&lt;div&gt;Material didático&amp;nbsp;&amp;nbsp;&lt;/div&gt;" vertex="1">
          <mxGeometry relative="1" x="0.0223" y="5" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-16" edge="1" parent="1" source="N1oVapyl2h7FQJmYYXLb-4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;exitPerimeter=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;entryPerimeter=0;" target="N1oVapyl2h7FQJmYYXLb-6">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="420" y="500" />
              <mxPoint x="670" y="500" />
              <mxPoint x="670" y="560" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-21" connectable="0" parent="N1oVapyl2h7FQJmYYXLb-16" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" value="Cadastro&lt;div&gt;Desempenho e&amp;nbsp; evolução&lt;/div&gt;" vertex="1">
          <mxGeometry relative="1" x="0.0333" y="-1" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-26" edge="1" parent="1" source="N1oVapyl2h7FQJmYYXLb-6" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.25;exitY=1;exitDx=0;exitDy=0;exitPerimeter=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;entryPerimeter=0;" target="N1oVapyl2h7FQJmYYXLb-1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="600" y="710" />
              <mxPoint x="40" y="710" />
              <mxPoint x="40" y="130" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="N1oVapyl2h7FQJmYYXLb-27" connectable="0" parent="N1oVapyl2h7FQJmYYXLb-26" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" value="Relatório" vertex="1">
          <mxGeometry relative="1" x="0.4439" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
