<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';

	let ordenes = $state([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state(null);
	let limit = 20;
	let offset = $state(0);

	async function fetchOrdenes() {
		loading = true;
		error = null;
		try {
			const data = await api.get('/admin/purchase-orders', { limit, offset });
			ordenes = data.items;
			total = data.total;
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function nextPage() {
		if (offset + limit < total) {
			offset += limit;
			fetchOrdenes();
		}
	}
	function prevPage() {
		if (offset > 0) {
			offset = Math.max(0, offset - limit);
			fetchOrdenes();
		}
	}

	onMount(fetchOrdenes);
</script>

<svelte:head>
	<title>Órdenes de Compra — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
		<div>
			<h1 class="font-oswald font-bold text-xl">Órdenes de Compra</h1>
			<p class="text-xs text-muted-foreground">Emitidas al aceptar pedidos (UC-AD15) o consolidar (RN-29) · congeladas si vendedor se da de baja (RN-27)</p>
		</div>
		<Button variant="outline" size="sm" onclick={fetchOrdenes}>Recargar</Button>
	</div>

	{#if error}
		<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
	{/if}

	{#if loading}
		<Skeleton class="h-64 w-full" />
	{:else}
		<Card class="overflow-hidden">
			<div class="overflow-auto">
				<table class="w-full text-sm">
					<thead class="bg-muted">
						<tr class="text-left font-oswald text-xs tracking-wide">
							<th class="px-3 py-2">Número</th>
							<th class="px-3 py-2">Total</th>
							<th class="px-3 py-2">Creada por</th>
							<th class="px-3 py-2">Fecha</th>
							<th class="px-3 py-2">Acciones</th>
						</tr>
					</thead>
					<tbody>
						{#each ordenes as oc}
							<tr class="border-t hover:bg-muted/50">
								<td class="px-3 py-2 font-mono text-xs font-bold">{oc.numero}</td>
								<td class="px-3 py-2 font-oswald font-bold">${Number(oc.total).toFixed(2)}</td>
								<td class="px-3 py-2 font-mono text-xs">{oc.created_by.slice(0, 8)}…</td>
								<td class="px-3 py-2 text-xs">{new Date(oc.created_at).toLocaleString()}</td>
								<td class="px-3 py-2"><a href="/ordenes/{oc.id}" class="border px-2 py-1 text-xs hover:bg-accent">Ver</a></td>
							</tr>
						{/each}
						{#if ordenes.length === 0}
							<tr><td colspan="5" class="px-3 py-6 text-center text-muted-foreground">Sin órdenes</td></tr>
						{/if}
					</tbody>
				</table>
			</div>
			<div class="flex items-center justify-between p-3 border-t bg-muted/20">
				<span class="text-xs">Total: {total} · Página {Math.floor(offset / limit) + 1} de {Math.ceil(total / limit) || 1}</span>
				<div class="flex gap-2">
					<Button variant="outline" size="sm" onclick={prevPage} disabled={offset === 0}>Anterior</Button>
					<Button variant="outline" size="sm" onclick={nextPage} disabled={offset + limit >= total}>Siguiente</Button>
				</div>
			</div>
		</Card>
	{/if}
</div>
