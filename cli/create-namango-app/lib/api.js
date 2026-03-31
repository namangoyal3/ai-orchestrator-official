const BASE_URL = process.env.NAMANGO_API_URL || 'https://ai-gateway-backend-production.up.railway.app';

async function request(path, options = {}) {
    const config = require('./config');
    const key = options.apiKey || config.get().apiKey || '';
    const res = await fetch(`${BASE_URL}${path}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': key,
            ...(options.headers || {}),
        },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

module.exports = {
    health: () => request('/health'),

    // Verifies the key is valid by calling an authenticated endpoint (not just /health which has no auth)
    verifyKey: (apiKey) => request('/v1/marketplace/agents', { apiKey }),

    agents: () => request('/v1/marketplace/agents'),
    tools: () => request('/v1/marketplace/tools'),
    llms: () => request('/v1/marketplace/llms'),
    repos: () => request('/v1/marketplace/repos'),
    toolDetail: (slug) => request(`/v1/marketplace/tools/${slug}`),

    query: (body) => request('/v1/query', { method: 'POST', body: JSON.stringify(body) }),
    history: (limit = 10) => request(`/v1/history?limit=${limit}`),

    // api_key removed from body — key is sent via X-API-Key header in request()
    architect: (prompt, optimization) =>
        request('/v1/architect/design', {
            method: 'POST',
            body: JSON.stringify({ prompt, optimization }),
        }),

    recommend: (product_description, use_cases) =>
        request('/v1/marketplace/recommend', {
            method: 'POST',
            body: JSON.stringify({ product_description, use_cases }),
        }),

    BASE_URL,
};
