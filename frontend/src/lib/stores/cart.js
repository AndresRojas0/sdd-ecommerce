import { writable, derived } from 'svelte/store';
import { api } from '$lib/api/client.js';
import { browser } from '$app/environment';

export const cart = writable(null);
export const cartLoading = writable(false);
export const cartError = writable(null);

export const cartCount = derived(cart, ($cart) => {
	if (!$cart?.items) return 0;
	return $cart.items.reduce((acc, it) => acc + Number(it.cantidad), 0);
});

export const cartTotal = derived(cart, ($cart) => $cart?.total ?? 0);

export async function fetchCart() {
	if (!browser) return;
	cartLoading.set(true);
	cartError.set(null);
	try {
		const data = await api.get('/carts/me');
		cart.set(data);
		return data;
	} catch (e) {
		if (e.status === 401) {
			cart.set(null);
			return null;
		}
		cartError.set(e.message);
		return null;
	} finally {
		cartLoading.set(false);
	}
}

export async function addToCart(product_id, cantidad = 1) {
	cartLoading.set(true);
	try {
		await api.post('/carts/me/items', { product_id, cantidad });
		await fetchCart();
	} catch (e) {
		cartError.set(e.message);
		throw e;
	} finally {
		cartLoading.set(false);
	}
}

export async function updateCartItem(item_id, cantidad) {
	cartLoading.set(true);
	try {
		await api.put(`/carts/me/items/${item_id}`, { cantidad });
		await fetchCart();
	} catch (e) {
		cartError.set(e.message);
		throw e;
	} finally {
		cartLoading.set(false);
	}
}

export async function removeCartItem(item_id) {
	cartLoading.set(true);
	try {
		await api.delete(`/carts/me/items/${item_id}`);
		await fetchCart();
	} catch (e) {
		cartError.set(e.message);
		throw e;
	} finally {
		cartLoading.set(false);
	}
}

export async function clearCart() {
	try {
		await api.delete('/carts/me');
		await fetchCart();
	} catch (e) {
		throw e;
	}
}
