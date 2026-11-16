# Create or validate the Elasticsearch index used by Spark Streaming v2.
# Run from repository root: .\scripts\create_es_index.ps1
# Non-destructive: existing indices are NOT deleted or overwritten.

$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:9200"
$indexName = "social_events_v1"
$indexUri = "$baseUrl/$indexName"

Write-Host "[1/3] Checking Elasticsearch at $baseUrl ..."
try {
    $null = Invoke-RestMethod -Method Get -Uri $baseUrl -TimeoutSec 10
} catch {
    throw "Elasticsearch is not reachable. Start Docker Compose first. Details: $($_.Exception.Message)"
}

# Check whether the index exists. HTTP 404 means it does not exist.
$indexExists = $true
try {
    $null = Invoke-RestMethod -Method Get -Uri "$indexUri/_mapping" -TimeoutSec 10
} catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404) {
        $indexExists = $false
    } else {
        throw "Could not check Elasticsearch index: $($_.Exception.Message)"
    }
}

if (-not $indexExists) {
    Write-Host "[2/3] Creating index '$indexName' ..."
    $mapping = @'
{
  "mappings": {
    "properties": {
      "event_id": {"type": "keyword"},
      "platform": {"type": "keyword"},
      "content_type": {"type": "keyword"},
      "text": {"type": "text"},
      "language": {"type": "keyword"},
      "created_at": {"type": "date"},
      "collected_at": {"type": "date"},
      "processed_at": {"type": "date"},
      "engagement": {
        "properties": {
          "likes": {"type": "long"},
          "replies": {"type": "long"},
          "shares": {"type": "long"}
        }
      },
      "sentiment_label": {"type": "keyword"},
      "sentiment_confidence": {"type": "float"},
      "processing_mode": {"type": "keyword"}
    }
  }
}
'@

    $response = Invoke-RestMethod -Method Put -Uri $indexUri -ContentType 'application/json' -Body $mapping -TimeoutSec 30
    if (-not $response.acknowledged) {
        throw "Elasticsearch did not acknowledge the index creation."
    }
    Write-Host "Index created: $indexName"
} else {
    Write-Host "[2/3] Index already exists; it will NOT be deleted or recreated."
}

Write-Host "[3/3] Checking timestamp mapping ..."
$indexMapping = Invoke-RestMethod -Method Get -Uri "$indexUri/_mapping" -TimeoutSec 10
$properties = $indexMapping.$indexName.mappings.properties

foreach ($fieldName in @('created_at', 'collected_at', 'processed_at')) {
    $field = $properties.$fieldName
    if ($null -eq $field -or $field.type -ne 'date') {
        throw "Wrong mapping: '$fieldName' must have type 'date'. Existing data was not modified."
    }
    Write-Host "OK: $fieldName = date"
}

Write-Host "SUCCESS: Elasticsearch index '$indexName' is ready."
