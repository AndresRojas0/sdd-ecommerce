import { writable } from 'svelte/store';
import { api } from '$lib/api/client.js';
import { browser } from '$app/environment';

export const user = writable(null);
export const authLoading = writable(false);
export const authError = writable(null);

export async function fetchMe() {
	if (!browser) return null;
	authLoading.set(true);
	authError.set(null);
	try {
		const data = await api.get('/auth/me');
		// verify role is admin or vendedor
		if (data.role !== 'administrador' && data.role !== 'vendedor') {
			user.set(null);
			authError.set('Acceso denegado: se requiere rol administrador o vendedor');
			return null;
		}
		user.set(data);
		return data;
	} catch (e) {
		if (e.status === 401 || e.status === 403) {
			// check if must_change_password
			const detail = e.data?.detail;
			if (detail?.code === 'MUST_CHANGE_PASSWORD') {
				authError.set('Debe cambiar su contraseña antes de continuar');
			} else if (detail?.code === 'ACCOUNT_DEACTIVATED') {
				authError.set('Cuenta desactivada');
			}
			user.set(null);
			return null;
		}
		authError.set(e.message);
		user.set(null);
		return null;
	} finally {
		authLoading.set(false);
	}
}

export async function login(email, password) {
	authLoading.set(true);
	authError.set(null);
	try {
		const res = await api.post('/auth/login', { email, password });
		const me = await fetchMe();
		// fetchMe already checks role
		if (!me) {
			// if login succeeded but role invalid, logout
			try {
				await api.post('/auth/logout', {});
			} catch {}
			throw new Error('Acceso denegado: rol no autorizado');
		}
		return res;
	} catch (e) {
		// handle MUST_CHANGE_PASSWORD and .local email validation
		const detail = e.data?.detail;
		if (Array.isArray(detail)) {
			// pydantic validation error (e.g. .local email)
			const msg = detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
			authError.set(msg);
			e.message = msg;
		} else if (detail?.code === 'MUST_CHANGE_PASSWORD') {
			authError.set('Debe cambiar su contraseña. Use el formulario de cambio.');
		} else if (detail && typeof detail === 'object' && detail.message) {
			authError.set(detail.message);
		} else {
			authError.set(e.message);
		}
		throw e;
	} finally {
		authLoading.set(false);
	}
}

export async function logout() {
	try {
		await api.post('/auth/logout', {});
	} catch {}
	user.set(null);
}
