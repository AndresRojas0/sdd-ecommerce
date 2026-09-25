// VITE_API_URL vacío ("") = URLs relativas: las llamadas pasan por el proxy
// de Vite (same-origin) y las cookies de sesión son first-party. Con `??`
// un "" se respeta en vez de caer al default (|| lo trataría como falsy).
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

// En Vercel, /categorias y /colecciones colisionan con páginas de la SPA
// (filesystem gana sobre rewrites) → viajan bajo /api/* (ver admin/vercel.json).
// Se activa SOLO con VITE_VERCEL_REWRITES=1 (env del proyecto en Vercel);
// dev local y compose siguen llamando las rutas directas.
const PATH_ALIASES = { '/categorias': '/api/categorias', '/colecciones': '/api/colecciones' };
const ALIASES_ACTIVE = import.meta.env.VITE_VERCEL_REWRITES === '1';

function resolvePath(path) {
	if (!ALIASES_ACTIVE) return path;
	for (const [from, to] of Object.entries(PATH_ALIASES)) {
		if (path === from || path.startsWith(from + '/') || path.startsWith(from + '?')) {
			return to + path.slice(from.length);
		}
	}
	return path;
}

function buildUrl(path, params) {
	path = resolvePath(path);
	// base = origin actual: permite API_URL relativo (proxy de dev)
	const url = new URL(`${API_URL}${path}`, window.location.origin);
	if (params) {
		Object.entries(params).forEach(([k, v]) => {
			if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v));
		});
	}
	return url.toString();
}

async function request(method, path, { params, body, headers = {} } = {}) {
	const url = buildUrl(path, params);
	const opts = {
		method,
		credentials: 'include',
		headers: { ...headers }
	};
	if (body !== undefined) {
		opts.headers['Content-Type'] = 'application/json';
		opts.body = JSON.stringify(body);
	}
	const res = await fetch(url, opts);
	const text = await res.text();
	let data;
	try {
		data = text ? JSON.parse(text) : null;
	} catch {
		data = text;
	}
	if (!res.ok) {
		const msg = data?.detail || data?.message || res.statusText;
		const err = new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
		err.status = res.status;
		err.data = data;
		throw err;
	}
	return data;
}

export const api = {
	get(path, params) {
		return request('GET', path, { params });
	},
	post(path, body, params) {
		return request('POST', path, { body, params });
	},
	put(path, body, params) {
		return request('PUT', path, { body, params });
	},
	patch(path, body, params) {
		return request('PATCH', path, { body, params });
	},
	delete(path, params) {
		return request('DELETE', path, { params });
	},
	API_URL
};
