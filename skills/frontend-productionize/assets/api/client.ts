import createClient from 'openapi-fetch';
import type { paths } from './schema';

// Create typed fetch client
export const api = createClient<paths>({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authentication interceptor
export function setAuthToken(token: string | null) {
  if (token) {
    api.use({
      onRequest({ request }) {
        request.headers.set('Authorization', `Bearer ${token}`);
        return request;
      },
    });
  }
}

// Add error interceptor
api.use({
  onResponse({ response }) {
    if (!response.ok) {
      console.error('API Error:', response.status, response.statusText);
    }
    return response;
  },
});
