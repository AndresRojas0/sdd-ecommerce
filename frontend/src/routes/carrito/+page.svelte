<script>
	import { onMount } from 'svelte';
	import { cart, cartTotal, fetchCart, updateCartItem, removeCartItem, clearCart } from '$lib/stores/cart.js';
	import { user } from '$lib/stores/auth.js';
	import { goto } from '$app/navigation';
	import Button from '$lib/components/ui/button.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import { api } from '$lib/api/client.js';

	let loading = $state(true);
	let error = $state(null);
	let confirming = $state(false);

	onMount(async () => {
		if (!$user) {
			await goto('/login');
			return;
		}
		try {
			await fetchCart();
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	});

	async function handleConfirm() {
		confirming = true;
		error = null;
		try {
			await api.post('/orders', {});
			await fetchCart();
			await goto('/mis-pedidos');
		} catch (e) {
			error = e.message;
		} finally {
			confirming = false;
		}
	}
</script>

<div class="max-w-[900px] mx-auto px-4 py-8">
	<h1 class="font-oswald font-bold text-2xl mb-6">Carrito</h1>

	{#if loading}
		<div class="flex flex-col gap-3">
			<Skeleton class="h-20 w-full" />
			<Skeleton class="h-20 w-full" />
		</div>
	{:else if error}
		<Alert variant="destructive"><p>{error}</p></Alert>
	{:else if !$cart || $cart.items.length === 0}
		<p class="text-muted-foreground">Tu carrito está vacío.</p>
		<div class="mt-4"><Button onclick={() => goto('/')}>Ir al catálogo</Button></div>
	{:else}
		<div class="flex flex-col gap-3">
			{#each $cart.items as it}
				<div class="border p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
					<div class="flex-1">
						<a href="/producto/{it.producto_slug}" class="font-bold hover:underline">{it.producto_titulo}</a>
						<div class="text-sm text-muted-foreground">
							Precio: ${Number(it.precio_unitario).toFixed(2)} — Subtotal: ${Number(it.subtotal).toFixed(
								2
							)}
						</div>
					</div>
					<div class="flex items-center gap-2">
						<input
							type="number"
							min="0.01"
							step="0.01"
							value={it.cantidad}
							onchange={(e) => updateCartItem(it.id, Number(e.target.value))}
							class="border px-2 py-1 w-20 text-sm"
						/>
						<Button variant="ghost" size="sm" onclick={() => removeCartItem(it.id)}>Quitar</Button>
					</div>
				</div>
			{/each}
		</div>

		<div class="mt-6 flex flex-col gap-4 border-t pt-4">
			<div class="flex justify-between font-oswald font-bold text-xl">
				<span>Total</span>
				<span>${Number($cartTotal).toFixed(2)}</span>
			</div>
			{#if error}
				<Alert variant="destructive">{error}</Alert>
			{/if}
			<div class="flex gap-3 flex-wrap">
				<Button onclick={handleConfirm} disabled={confirming}>{confirming ? 'Confirmando…' : 'Confirmar pedido'}</Button>
				<Button variant="outline" onclick={async () => { await clearCart(); }}>Vaciar carrito</Button>
				<Button variant="ghost" onclick={() => goto('/')}>Seguir comprando</Button>
			</div>
		</div>
	{/if}
</div>
