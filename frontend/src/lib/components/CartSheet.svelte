<script>
	import Sheet from '$lib/components/ui/sheet.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Separator from '$lib/components/ui/separator.svelte';
	import { cart, cartTotal, fetchCart, removeCartItem } from '$lib/stores/cart.js';
	import { goto } from '$app/navigation';

	let { open = $bindable(false) } = $props();

	$effect(() => {
		if (open) fetchCart();
	});

	async function goCart() {
		open = false;
		await goto('/carrito');
	}
	async function confirmOrder() {
		try {
			const { api } = await import('$lib/api/client.js');
			await api.post('/orders', {});
			await fetchCart();
			open = false;
			await goto('/mis-pedidos');
		} catch (e) {
			alert(e.message);
		}
	}
</script>

<Sheet bind:open>
	<div class="p-4 pt-12 flex flex-col h-full gap-4">
		<h2 class="font-oswald font-bold text-xl">Carrito</h2>
		<Separator />
		{#if !$cart || $cart.items.length === 0}
			<p class="text-sm text-muted-foreground">Tu carrito está vacío.</p>
			<Button variant="outline" onclick={goCart}>Ir al catálogo</Button>
		{:else}
			<div class="flex-1 overflow-auto flex flex-col gap-3">
				{#each $cart.items as it}
					<div class="flex justify-between gap-2 border p-2 text-sm">
						<div class="flex-1">
							<div class="font-bold line-clamp-1">{it.producto_titulo || it.product_id}</div>
							<div class="text-muted-foreground">x {it.cantidad} — ${Number(it.precio_unitario).toFixed(2)}</div>
						</div>
						<div class="text-right">
							<div class="font-bold">${Number(it.subtotal).toFixed(2)}</div>
							<button class="text-xs text-destructive hover:underline" onclick={() => removeCartItem(it.id)}>Quitar</button>
						</div>
					</div>
				{/each}
			</div>
			<Separator />
			<div class="flex justify-between font-oswald font-bold text-lg">
				<span>Total</span>
				<span>${Number($cartTotal).toFixed(2)}</span>
			</div>
			<div class="flex flex-col gap-2">
				<Button onclick={confirmOrder}>Confirmar pedido</Button>
				<Button variant="outline" onclick={goCart}>Ver carrito completo</Button>
			</div>
		{/if}
	</div>
</Sheet>
