const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function buildUrl(path, params) {
	const url = new URL(`${API_URL}${path}`);
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
