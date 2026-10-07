const JSON_HEADERS = { 'Content-Type': 'application/json' }

export async function scanText(content, sourceType = 'text') {
  const response = await fetch('/api/scan', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ content, source_type: sourceType })
  })
  return readResponse(response)
}

export async function scanFile(file) {
  const form = new FormData()
  form.append('file', file)
  const response = await fetch('/api/scan/file', { method: 'POST', body: form })
  return readResponse(response)
}

export async function getHistory() {
  const response = await fetch('/api/history?limit=30')
  return readResponse(response)
}

export async function getStats() {
  const response = await fetch('/api/stats')
  return readResponse(response)
}

export async function getAttackCatalog() {
  const response = await fetch('/api/attacks')
  return readResponse(response)
}

export async function runTestSuite() {
  const response = await fetch('/api/test-suite/run', { method: 'POST' })
  return readResponse(response)
}

async function readResponse(response) {
  const data = await response.json().catch(() => ({ detail: 'Unexpected server response.' }))
  if (!response.ok) throw new Error(data.detail || 'Request failed.')
  return data
}
