# Адаптер GERON для нейропроцессора под Windows. Настройки: device.json в формате geron.runtime.json.
#   device.ps1 observe           факты по одному в строке, BLOCK <текст> для блокировок
#   device.ps1 run <ОПЕРАЦИЯ>    код выхода 0 при успехе; при известной ошибке последняя строка ERROR:<КОД>
param([string]$Mode, [string]$Op)
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$cfgPath = if ($env:NPU_DEVICE_CONF) { $env:NPU_DEVICE_CONF } else { Join-Path $PSScriptRoot 'device.json' }
$cfg = Get-Content -Raw -Encoding UTF8 $cfgPath | ConvertFrom-Json
$p = if ($env:NPU_PROJECT) { $cfg.projects | Where-Object id -eq $env:NPU_PROJECT } else { $cfg.projects[0] }
if (-not $p) { Write-Output 'BLOCK проект не найден в настройках'; exit 1 }
if ($p.environment) { foreach ($k in $p.environment.PSObject.Properties) { Set-Item "env:$($k.Name)" $k.Value } }
$repo = $p.repositoryPath; $branch = $p.gitBranch; $remote = $p.gitRemote; $res = $p.targetResourceName
$app = $p.aspireAppHostProjectPath; $cfgName = $p.configuration; $wd = if ($p.workingDirectory -and (Test-Path $p.workingDirectory)) { $p.workingDirectory } else { $repo }
function G { & git -C $repo @args }
function Target {
    if ($p.targetProjectPath) { return @($p.targetProjectPath) }
    return @(Get-ChildItem -Path $repo -Recurse -Filter "$res.csproj" -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '[\\/](bin|obj)[\\/]' } | ForEach-Object FullName)
}
function AspireWait([string]$status, [int]$t) { & aspire wait $res --status $status --timeout $t --apphost $app --non-interactive *> $null; return $LASTEXITCODE -eq 0 }
function Health {
    if (-not $p.healthUrl) { return $true }
    try { $a = @{ Uri = $p.healthUrl; TimeoutSec = 5; UseBasicParsing = $true }
        return (Invoke-WebRequest @a).StatusCode -lt 400 } catch { return $false }
}
function Observe {
    if (-not (Test-Path (Join-Path $repo '.git'))) {
        'REPOSITORY_MISSING'
        if ($p.cloneUrl) { 'CLONE_CONFIGURED' } else { 'BLOCK репозиторий отсутствует и cloneUrl не задан' }
    } else {
        'REPOSITORY_EXISTS'
        if ((G rev-parse --abbrev-ref HEAD) -eq $branch) { 'ON_TARGET_BRANCH' } else { "BLOCK текущая ветка не совпадает с $branch" }
        $merge = Test-Path (Join-Path $repo '.git/MERGE_HEAD')
        if (-not (G status --porcelain)) { 'WORKTREE_CLEAN' } else { 'WORKTREE_DIRTY'; if (-not $merge) { 'BLOCK рабочая копия содержит локальные изменения' } }
        if ($merge) {
            'MERGE_IN_PROGRESS'
            if (-not (G diff --name-only --diff-filter=U) -and -not (G diff --name-only)) { 'MERGE_READY_TO_COMMIT'; 'MERGE_COMPLETION_ALLOWED' } else { 'BLOCK слияние нельзя завершить автоматически' }
        }
        G fetch -q $remote $branch 2>$null
        if ($LASTEXITCODE -eq 0) {
            $c = (G rev-list --left-right --count HEAD...FETCH_HEAD) -split '\s+'; $ahead = [int]$c[0]; $behind = [int]$c[1]
            if (-not $merge) { 'GIT_PULL_REQUIRED' }
            if ($behind -gt 0 -and $ahead -eq 0) { 'GIT_UPDATE_REQUIRED' }
            if ($behind -gt 0 -and $ahead -gt 0 -and -not $merge) { 'GIT_DIVERGED' }
        } else { "BLOCK удалённая ветка $remote/$branch недоступна" }
        $t = @(Target)
        if ($t.Count -eq 0) { "BLOCK проект $res.csproj не найден" }
        elseif ($t.Count -gt 1) { "BLOCK проект $res.csproj неоднозначен" }
        elseif ([IO.Path]::GetFullPath($t[0]) -eq [IO.Path]::GetFullPath($app)) { 'BLOCK целевой проект совпадает с AppHost, останавливать его нельзя' }
    }
    if (-not $app) { 'BLOCK AppHost не настроен' }
    if (-not (Get-Command aspire -ErrorAction SilentlyContinue)) { 'BLOCK Aspire CLI недоступен'; 'ASPIRE_STOPPED' }
    else {
        & aspire describe $res --format Json --apphost $app --non-interactive *> $null
        if ($LASTEXITCODE -ne 0) { "BLOCK ресурс Aspire $res не найден"; 'ASPIRE_STOPPED' }
        elseif (AspireWait up 1) { 'ASPIRE_RUNNING' }
        elseif (AspireWait down 1) { 'ASPIRE_STOPPED' }
        else { 'SERVICE_STARTING' }
    }
    'NO_OPERATION_ERROR'
}
function Fail([string]$code) { Write-Output $code; exit 1 }
function Run([string]$o) {
    Set-Location $wd
    $t = (@(Target))[0]
    switch ($o) {
        'GIT_CLONE' { & git clone -q -b $branch $p.cloneUrl $repo; if ($LASTEXITCODE) { Fail 'ERROR:GIT_NETWORK' } }
        'GIT_PULL_MAIN' {
            G fetch -q $remote $branch; if ($LASTEXITCODE) { Fail 'ERROR:GIT_NETWORK' }
            G merge -q --no-edit FETCH_HEAD
            if ($LASTEXITCODE) { if (G diff --name-only --diff-filter=U) { Fail 'ERROR:GIT_MERGE_CONFLICT' } else { Fail 'ERROR:GIT_DIVERGED' } }
        }
        'GIT_COMPLETE_MERGE' { G commit -q --no-edit; if ($LASTEXITCODE) { Fail 'ERROR:GIT_MERGE_NOT_READY' } }
        'ASPIRE_STOP' { & aspire resource $res stop --apphost $app; if ($LASTEXITCODE) { exit 1 }; if (-not (AspireWait down 30)) { Write-Output 'ресурс не остановился'; exit 1 } }
        'DOTNET_CLEAN' { & dotnet clean $t -c $cfgName; if ($LASTEXITCODE) { exit 1 } }
        'DOTNET_RESTORE' { & dotnet restore $t; if ($LASTEXITCODE) { exit 1 } }
        'DOTNET_BUILD' { & dotnet build $t -c $cfgName --no-restore --verbosity quiet '-clp:ErrorsOnly;Summary'; if ($LASTEXITCODE) { exit 1 } }
        'ASPIRE_START' { & aspire resource $res start --apphost $app; if ($LASTEXITCODE) { exit 1 } }
        'WAIT_SERVICE_READY' {
            $limit = if ($p.healthTimeoutSeconds) { [int]$p.healthTimeoutSeconds } else { 90 }
            for ($i = 0; $i -lt $limit; $i++) { if (AspireWait up 1) { exit 0 } }
            Write-Output 'ресурс не поднялся за отведённое время'; exit 1
        }
        'HEALTH_CHECK' {
            $limit = if ($p.healthTimeoutSeconds) { [int]$p.healthTimeoutSeconds } else { 90 }; $need = if ($p.healthConsecutiveSuccesses) { [int]$p.healthConsecutiveSuccesses } else { 3 }; $ok = 0
            for ($i = 0; $i -lt $limit; $i++) {
                if ((AspireWait healthy 1) -and (Health)) { $ok++; if ($ok -ge $need) { exit 0 } } else { $ok = 0 }
                Start-Sleep -Milliseconds 300
            }
            Write-Output 'проверка здоровья не прошла'; exit 1
        }
        'WAIT_NETWORK' { Start-Sleep -Seconds 5 }
        default { Write-Output "неизвестная операция $o"; exit 2 }
    }
    exit 0
}
switch ($Mode) { 'observe' { Observe; exit 0 } 'run' { Run $Op } default { Write-Output 'observe | run <операция>'; exit 2 } }
