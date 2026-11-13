# Test Amazon SP-API, indépendant de Syllig Vente : tourne sur le PC, n'envoie rien ailleurs qu'à Amazon.
# Les codes sont tapés ou collés (clic droit) dans cette fenêtre ; ils ne sont ni affichés ni enregistrés.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
function Clair($x) { [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($x)) }
Write-Host ""
Write-Host "Test Amazon SP-API (independant de Syllig Vente)"
Write-Host "Collez chaque code par un clic droit, puis Entree."
Write-Host ""
$id = Read-Host "Identifiant client (LWA)"
$secret = Read-Host "Secret client (LWA)" -AsSecureString
$jeton = Read-Host "Jeton de rafraichissement" -AsSecureString
try {
  $t = Invoke-RestMethod -Method Post -Uri "https://api.amazon.com/auth/o2/token" -Body @{
    grant_type = "refresh_token"; refresh_token = (Clair $jeton); client_id = $id.Trim(); client_secret = (Clair $secret) }
  Write-Host "1. Identification : OK" -ForegroundColor Green
} catch {
  Write-Host "1. Identification : REFUSEE ($($_.Exception.Message))" -ForegroundColor Red
  Read-Host "Appuyez sur Entree pour fermer"; exit
}
foreach ($region in @("eu", "na", "fe")) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri "https://sellingpartnerapi-$region.amazon.com/sellers/v1/marketplaceParticipations" `
      -Headers @{ "x-amz-access-token" = $t.access_token }
    Write-Host "2. Compte vendeur, serveurs $($region.ToUpper()) : OK" -ForegroundColor Green
    ($r.Content | ConvertFrom-Json).payload | ForEach-Object { Write-Host "   - $($_.marketplace.name)" }
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host "2. Compte vendeur, serveurs $($region.ToUpper()) : refuse ($code)" -ForegroundColor Red
  }
}
Write-Host ""
Read-Host "Appuyez sur Entree pour fermer"
