const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail ?? `Request failed (${response.status})`) }
  if (response.status === 204) return undefined as T
  return response.json()
}
export const api = {
  health: () => request<{status:string,version:string}>('/api/health'),
  agents: () => request<any[]>('/api/agents'),
  registry: () => request<{entrypoints:string[]}>('/api/agents/registry'),
  createAgent: (body: any) => request<any>('/api/agents', {method:'POST',body:JSON.stringify(body)}),
  discoverAgent: (endpoint:string, timeout=5) => request<any>('/api/agents/discover', {method:'POST',body:JSON.stringify({endpoint,timeout})}),
  testConnection: (endpoint:string, timeout=5) => request<any>('/api/agents/test-connection', {method:'POST',body:JSON.stringify({endpoint,timeout})}),
  deleteAgent: (id:string) => request<void>(`/api/agents/${id}`, {method:'DELETE'}),
  updateAgent: (id:string, body:any) => request<any>(`/api/agents/${id}`, {method:'PATCH',body:JSON.stringify(body)}),
  suites: () => request<any[]>('/api/suites'),
  createSuite: (name:string, body:any) => request<any>(`/api/suites?name=${encodeURIComponent(name)}`, {method:'POST',body:JSON.stringify(body)}),
  evaluations: () => request<any[]>('/api/evaluations'),
  compatibility: (body:any) => request<any>('/api/compatibility', {method:'POST',body:JSON.stringify(body)}),
  run: (body:any) => request<any>('/api/evaluations', {method:'POST',body:JSON.stringify(body)}),
  evaluation: (id:string) => request<any>(`/api/evaluations/${id}`),
}
