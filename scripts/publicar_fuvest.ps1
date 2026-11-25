param(
    [Parameter(Mandatory = $true)][string]$Projeto,
    [switch]$ConfigurarBanco
)
$ErrorActionPreference = "Stop"
function Executar {
    param([string]$Programa, [string[]]$Argumentos)
    & $Programa @Argumentos
    if ($LASTEXITCODE -ne 0) { throw "Falha em $Programa. Corrija o erro exibido e execute novamente." }
}
$Pacote = Join-Path $PSScriptRoot "evolua-fuvest.bundle"
if (!(Test-Path $Pacote)) { throw "Coloque evolua-fuvest.bundle na mesma pasta deste script." }
Get-Command git, gh -ErrorAction Stop | Out-Null
Set-Location $Projeto
$Alteracoes = & git status --porcelain
if ($LASTEXITCODE -ne 0) { throw "Informe a pasta do repositório clonado." }
if ($Alteracoes) { throw "Salve as alterações locais em um commit antes de integrar a FUVEST." }
& gh auth status 2>$null
if ($LASTEXITCODE -ne 0) { Executar gh @("auth", "login", "--hostname", "github.com", "--web") }
$Repositorio = "EduMab/Projeto-De-Extensao-Em-Criacao-De-Sistemas"
$Remoto = & git remote get-url origin
if ($LASTEXITCODE -ne 0 -or $Remoto -notmatch 'github.com[:/]EduMab/Projeto-De-Extensao-Em-Criacao-De-Sistemas(?:\.git)?$') {
    throw "A pasta precisa ser um clone do repositório do grupo."
}
Executar git @("fetch", "origin", "main")
Executar git @("fetch", $Pacote, "refs/heads/provas/fuvest")
& git show-ref --verify --quiet refs/heads/provas/fuvest
if ($LASTEXITCODE -eq 0) {
    Executar git @("switch", "provas/fuvest")
    Executar git @("merge", "--ff-only", "FETCH_HEAD")
} else {
    Executar git @("switch", "-c", "provas/fuvest", "FETCH_HEAD")
}
Executar git @("push", "-u", "origin", "provas/fuvest")

if ($ConfigurarBanco) {
    Write-Host "Informe os dados do MySQL compartilhado. Os valores serão salvos como secrets do ambiente fuvest."
    & gh api "repos/$Repositorio/environments/fuvest" --silent 2>$null
    if ($LASTEXITCODE -ne 0) {
        Executar gh @("api", "--method", "PUT", "repos/$Repositorio/environments/fuvest", "--silent")
    }
    foreach ($Nome in @("DB_HOST", "DB_PORT", "DB_NAME", "DB_USUARIO", "DB_SENHA")) {
        Executar gh @("secret", "set", $Nome, "--repo", $Repositorio, "--env", "fuvest")
    }
    Write-Host "Para certificado próprio, configure também DB_SSL_CA no ambiente fuvest do GitHub."
}
$Numero = & gh pr list --repo $Repositorio --head provas/fuvest --base main --state open --json number --jq ".[0].number"
if ($LASTEXITCODE -ne 0) { throw "Falha ao consultar pull requests." }
if (!$Numero) {
    Executar gh @("pr", "create", "--repo", $Repositorio, "--base", "main", "--head", "provas/fuvest",
        "--title", "Importa dez edições FUVEST e automatiza a publicação",
        "--body", "Integra 890 questões oficiais, com 886 aptas para simulados semanais de 40 questões. Valida carga e reexecução no MySQL, executa os testes Java e aplica a carga na main usando os secrets do ambiente fuvest.")
    $Numero = & gh pr list --repo $Repositorio --head provas/fuvest --base main --state open --json number --jq ".[0].number"
    if ($LASTEXITCODE -ne 0 -or !$Numero) { throw "Confira o pull request criado no GitHub." }
}
# Aguarda o registro inicial dos checks para que uma PR recém-criada seja testada.
$Checks = $null
for ($Tentativa = 0; $Tentativa -lt 12; $Tentativa++) {
    $Checks = & gh pr checks $Numero --repo $Repositorio --json name 2>$null
    if ($Checks -and $Checks -ne "[]") { break }
    Start-Sleep -Seconds 5
}
if (!$Checks -or $Checks -eq "[]") { throw "Os testes ainda não foram registrados. Execute o script novamente." }
Executar gh @("pr", "checks", $Numero, "--repo", $Repositorio, "--watch", "--fail-fast")
Executar gh @("pr", "merge", $Numero, "--repo", $Repositorio, "--squash")
Write-Host "Integração concluída. A carga será executada pelo workflow Publicar acervo FUVEST."
Write-Host "Acompanhe em https://github.com/$Repositorio/actions"
