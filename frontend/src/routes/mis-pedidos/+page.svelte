<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import { user } from '$lib/stores/auth.js';
	import { goto } from '$app/navigation';
	import Badge from '$lib/components/ui/badge.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Button from '$lib/components/ui/button.svelte';

	let pedidos = $state([]);
	let total = $state(0);
	let loading = $state(true);
	let error = $state(null);

	onMount(async () => {
		if (!$user) {
			await goto('/login');
			return;
		}
		try {
			const data = await api.get('/orders', { limit: 50, offset: 0 });
			// data may be {items} or paginated
			if (Array.isArray(data)) pedidos = data;
			else {
				pedidos = data.items || data.pedidos || [];
				total = data.total || pedidos.length;
			}
		} catch (e) {
			if (e.status === 401) await goto('/login');
			else error = e.message;
		} finally {
			loading = false;
		}
	});

	function badgeVariant(estado) {
		if (estado === 'aceptado') return 'default';
		if (estado === 'rechazado') return 'destructive';
		return 'secondary';
	}
</script>

<div class="max-w-[1000px] mx-auto px-4 py-8">
	<h1 class="font-oswald font-bold text-2xl mb-6">Mis Pedidos</h1>

	{#if loading}
		<div class="grid gap-3">
			<Skeleton class="h-24 w-full" />
			<Skeleton class="h-24 w-full" />
		</div>
	{:else if error}
		<Alert variant="destructive"><p>{error}</p></Alert>
	{:else if pedidos.length === 0}
		<div class="text-center py-16 flex flex-col gap-4 items-center">
			<p class="text-muted-foreground">Aún no tenés pedidos.</p>
			<Button onclick={() => goto('/')}>Ir al catálogo</Button>
		</div>
	{:else}
		<div class="flex flex-col gap-4">
			{#each pedidos as p}
				<div class="border p-4 flex flex-col gap-2 bg-card">
					<div class="flex justify-between items-start gap-2">
						<span class="font-mono text-xs">#{String(p.id).slice(0, 8)}</span>
						<Badge variant={badgeVariant(p.estado)}>{p.estado}</Badge>
					</div>
					<div class="text-sm">
						<div>Total: <span class="font-bold">${Number(p.total ?? p.subtotal ?? 0).toFixed(2)}</span></div>
						<div class="text-muted-foreground text-xs">{new Date(p.created_at).toLocaleString('es-AR')}</div>
						{#if p.motivo_rechazo}
							<div class="mt-1 text-destructive text-xs">Motivo rechazo: {p.motivo_rechazo}</div>
						{/if}
					</div>
					{#if p.items?.length}
						<ul class="text-xs list-disc ml-4">
							{#each p.items as it}
								<li>{it.producto_titulo || it.product_id} x {it.cantidad} — ${Number(it.subtotal ?? 0).toFixed(2)}</li>
							{/each}
						</ul>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
