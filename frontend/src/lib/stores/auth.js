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
		user.set(data);
		return data;
	} catch (e) {
		if (e.status === 401 || e.status === 403) {
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
		// fetch user after login (cookies set)
		await fetchMe();
		return res;
	} catch (e) {
		authError.set(e.message);
		throw e;
	} finally {
		authLoading.set(false);
	}
}

export async function register(payload) {
	authLoading.set(true);
	authError.set(null);
	try {
		const res = await api.post('/auth/register', payload);
		return res;
	} catch (e) {
		authError.set(e.message);
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
	if (browser) {
		// clear local cart badge
		try {
			localStorage.removeItem('cart');
		} catch {}
	}
}
