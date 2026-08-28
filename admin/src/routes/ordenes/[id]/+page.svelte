<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';

	let oc = $state(null);
	let loading = $state(true);
	let error = $state(null);
	let id = $derived($page.params.id);

	async function fetch() {
		loading = true;
		error = null;
		try {
			oc = await api.get(`/admin/purchase-orders/${id}`);
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	onMount(fetch);
</script>

<svelte:head>
	<title>OC {oc?.numero ?? id.slice(0,8)} — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<a href="/ordenes" class="text-sm underline">← Volver a órdenes</a>

	{#if loading}
		<Skeleton class="h-64 w-full" />
	{:else if error}
		<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
	{:else if oc}
		<Card class="p-4 flex flex-col gap-3">
			<div class="flex flex-col md:flex-row justify-between gap-3">
				<div>
					<h1 class="font-oswald font-bold text-xl">{oc.numero}</h1>
					<p class="font-mono text-xs text-muted-foreground">{oc.id} · Creada por {oc.created_by}</p>
					<p class="text-xs">Fecha: {new Date(oc.created_at).toLocaleString()}</p>
				</div>
				<div class="font-oswald font-bold text-lg">Total: ${Number(oc.total).toFixed(2)}</div>
			</div>

			{#if oc.pedidos}
				<div class="border-t pt-3">
					<h3 class="font-oswald font-bold text-sm mb-2">Pedidos vinculados ({oc.pedidos.length}) — RN-29 si N>1 es consolidada</h3>
					<div class="flex flex-col gap-3">
						{#each oc.pedidos as p}
							<Card class="p-3 border-l-4 border-l-[#e85d04]">
								<div class="flex justify-between items-start">
									<div>
										<a href="/pedidos/{p.id}" class="font-mono text-xs underline">{p.id}</a>
										<Badge variant={p.estado === 'aceptado' ? 'secondary' : 'outline'} class="ml-2">{p.estado}</Badge>
										<p class="text-xs">Cliente: {p.user_id} · Vendedor: {p.vendedor_id || '—'}</p>
									</div>
									<span class="font-bold">${Number(p.total).toFixed(2)}</span>
								</div>
								<div class="mt-2 overflow-auto">
									<table class="w-full text-xs">
										<thead><tr class="border-b"><th class="text-left p-1">Producto</th><th class="text-left p-1">Cant.</th><th class="text-left p-1">P.Unit</th><th class="text-left p-1">Subtotal</th></tr></thead>
										<tbody>
											{#each p.items as it}
												<tr class="border-b">
													<td class="p-1">{it.producto_titulo || it.product_id.slice(0,8)}</td>
													<td class="p-1">{it.cantidad}</td>
													<td class="p-1">${Number(it.precio_unitario).toFixed(2)}</td>
													<td class="p-1">${Number(it.subtotal).toFixed(2)}</td>
												</tr>
											{/each}
										</tbody>
									</table>
								</div>
							</Card>
						{/each}
					</div>
				</div>
			{/if}
		</Card>
	{/if}
</div>
