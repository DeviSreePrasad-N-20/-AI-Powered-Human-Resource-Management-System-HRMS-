const API_BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed: ${response.status}`)
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    return (await response.json()) as T
  }

  return undefined as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  postJson: <T>(path: string, data: unknown) =>
    request<T>(path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }),
  putJson: <T>(path: string, data: unknown) =>
    request<T>(path, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }),
  patchJson: <T>(path: string, data: unknown) =>
    request<T>(path, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }),
  postForm: <T>(path: string, data: FormData) =>
    request<T>(path, {
      method: 'POST',
      body: data,
    }),
}

export { API_BASE }
