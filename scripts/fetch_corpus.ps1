param(
    [int]$Limit = 20
)

$BaseUrl = "https://www.cert.ssi.gouv.fr"
$ListUrl = "$BaseUrl/avis/"
$OutputDir = "corpus/raw"

if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "Récupération des avis CERT-FR..."
Write-Host "Nombre maximum d'avis : $Limit"
Write-Host "Dossier de sortie : $OutputDir"
Write-Host ""

$avisLinks = @()
$page = 1

while ($avisLinks.Count -lt $Limit -and $page -le 10) {
    if ($page -eq 1) {
        $url = $ListUrl
    } else {
        $url = "$ListUrl?page=$page"
    }

    Write-Host "Lecture de la page : $url"

    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing
        $html = $response.Content

        $matches = [regex]::Matches($html, 'href="(/avis/CERTFR-[0-9]{4}-AVI-[0-9]{4}/)"')

        foreach ($match in $matches) {
            $link = $BaseUrl + $match.Groups[1].Value

            if ($avisLinks -notcontains $link) {
                $avisLinks += $link
            }

            if ($avisLinks.Count -ge $Limit) {
                break
            }
        }
    }
    catch {
        Write-Host "Erreur pendant la lecture de $url"
        Write-Host $_.Exception.Message
    }

    $page++
}

Write-Host ""
Write-Host "Avis trouvés : $($avisLinks.Count)"
Write-Host ""

$index = 1

foreach ($avisUrl in $avisLinks) {
    Write-Host "Téléchargement $index/$($avisLinks.Count) : $avisUrl"

    try {
        $avisResponse = Invoke-WebRequest -Uri $avisUrl -UseBasicParsing
        $avisHtml = $avisResponse.Content

        $certIdMatch = [regex]::Match($avisUrl, 'CERTFR-[0-9]{4}-AVI-[0-9]{4}')
        $certId = $certIdMatch.Value

        $outputFile = Join-Path $OutputDir "$certId.html"

        $avisHtml | Set-Content -Path $outputFile -Encoding UTF8
    }
    catch {
        Write-Host "Erreur pendant le téléchargement de $avisUrl"
        Write-Host $_.Exception.Message
    }

    $index++
}

Write-Host ""
Write-Host "Récupération terminée."
Write-Host "Les fichiers sont dans : $OutputDir"