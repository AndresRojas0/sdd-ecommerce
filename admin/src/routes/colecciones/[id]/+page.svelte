<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';

	let id = $derived($page.params.id);
	let coleccion = $state(null);
	let loading = $state(true);
	let error = $state(null);
	let success = $state(null);

	let searchQuery = $state('');
	let searchResults = $state([]);
	let searching = $state(false);
	let addingId = $state(null);
	let reorderSaving = $state(false);

	// edit inline for destacada
	async function fetchColeccion() {
		loading = true;
		error = null;
		try {
			coleccion = await api.get(`/colecciones/${id}`);
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	async function toggleDestacada() {
		if (!coleccion) return;
		try {
			await api.put(`/colecciones/${coleccion.id}`, { destacada: !coleccion.destacada });
			await fetchColeccion();
		} catch (e) {
			error = e.message;
		}
	}

	async function searchProducts() {
		if (!searchQuery.trim()) {
			searchResults = [];
			return;
		}
		searching = true;
		try {
			const data = await api.get('/products', { q: searchQuery.trim(), limit: 10, include_hidden: true });
			// data.items
			const items = data.items || data || [];
			// filter out already in collection
			const existingIds = new Set((coleccion?.productos || []).map((p) => p.id));
			searchResults = items.filter((p) => !existingIds.has(p.id));
		} catch (e) {
			error = e.message;
		} finally {
			searching = false;
		}
	}

	async function addProduct(productId) {
		addingId = productId;
		error = null;
		success = null;
		try {
			const maxOrden = Math.max(0, ...(coleccion.productos || []).map((p) => p.orden ?? 0));
			await api.post(`/colecciones/${coleccion.id}/productos`, { product_id: productId, orden: maxOrden + 1 });
			success = 'Producto agregado';
			searchQuery = '';
			searchResults = [];
			await fetchColeccion();
			setTimeout(() => (success = null), 2000);
		} catch (e) {
			const d = e.data?.detail;
			error = typeof d === 'string' ? d : d ? JSON.stringify(d) : e.message;
		} finally {
			addingId = null;
		}
	}

	async function removeProduct(productId) {
		if (!confirm('¿Quitar producto de la colección?')) return;
		try {
			await api.delete(`/colecciones/${coleccion.id}/productos/${productId}`);
			await fetchColeccion();
		} catch (e) {
			error = e.message;
		}
	}

	function moveUp(index) {
		if (index <= 0 || !coleccion?.productos) return;
		const arr = [...coleccion.productos];
		const tmp = arr[index - 1];
		arr[index - 1] = arr[index];
		arr[index] = tmp;
		coleccion.productos = arr;
	}

	function moveDown(index) {
		if (!coleccion?.productos || index >= coleccion.productos.length - 1) return;
		const arr = [...coleccion.productos];
		const tmp = arr[index + 1];
		arr[index + 1] = arr[index];
		arr[index] = tmp;
		coleccion.productos = arr;
	}

	async function saveReorder() {
		if (!coleccion?.productos?.length) return;
		reorderSaving = true;
		error = null;
		try {
			const product_ids = coleccion.productos.map((p) => p.id);
			await api.patch(`/colecciones/${coleccion.id}/productos/reorder`, { product_ids });
			success = 'Orden guardado';
			await fetchColeccion();
			setTimeout(() => (success = null), 2000);
		} catch (e) {
			const d = e.data?.detail;
			error = typeof d === 'string' ? d : d ? JSON.stringify(d) : e.message;
		} finally {
			reorderSaving = false;
		}
	}

	onMount(fetchColeccion);
</script>

<svelte:head>
	<title>{coleccion?.nombre ?? 'Colección'} — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<a href="/colecciones" class="text-sm underline">← Volver a colecciones</a>

	{#if loading}
		<Skeleton class="h-64 w-full" />
	{:else if error && !coleccion}
		<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
	{:else if coleccion}
		<Card class="p-4 flex flex-col gap-3">
			<div class="flex flex-col md:flex-row justify-between gap-3">
				<div>
					<h1 class="font-oswald font-bold text-xl">{coleccion.nombre}</h1>
					<p class="font-mono text-xs text-muted-foreground">{coleccion.slug} · {coleccion.id}</p>
					<p class="text-sm text-muted-foreground mt-1">{coleccion.descripcion || 'Sin descripción'}</p>
					{#if coleccion.imagen}
						<img src={coleccion.imagen} alt={coleccion.nombre} class="max-h-40 object-contain border bg-muted mt-2" />
					{/if}
				</div>
				<div class="flex flex-col gap-2 items-start md:items-end">
					<div class="flex gap-2">
						<Badge variant={coleccion.destacada ? 'secondary' : 'outline'}>{coleccion.destacada ? '★ destacada' : 'no destacada'}</Badge>
						<Badge variant="outline">{coleccion.productos_count ?? coleccion.productos?.length ?? 0} productos</Badge>
					</div>
					<Button size="sm" variant="outline" onclick={toggleDestacada}>{coleccion.destacada ? 'Quitar destacada' : 'Marcar destacada'}</Button>
					<span class="text-xs text-muted-foreground">Creada: {new Date(coleccion.created_at).toLocaleString()}</span>
					<span class="text-xs text-muted-foreground">Actualizada: {new Date(coleccion.updated_at).toLocaleString()}</span>
				</div>
			</div>
		</Card>

		{#if error}<Alert variant="destructive"><p class="text-sm whitespace-pre-wrap">{error}</p></Alert>{/if}
		{#if success}<Alert><p class="text-sm">{success}</p></Alert>{/if}

		<Card class="p-4 flex flex-col gap-3">
			<h2 class="font-oswald font-bold">Productos en la colección (ordenado por orden)</h2>
			<p class="text-xs text-muted-foreground">RN-39 · N:M coleccion_productos (orden) · Reordenar con ↑↓ y guardar · DELETE /colecciones/{"{id}"}/productos/{"{product_id}"} · PATCH /colecciones/{"{id}"}/productos/reorder</p>

			<div class="flex flex-col md:flex-row gap-2">
				<Input bind:value={searchQuery} placeholder="Buscar producto por título (GET /products?q=...)" class="md:max-w-sm" />
				<Button size="sm" onclick={searchProducts} disabled={searching}>{searching ? 'Buscando…' : 'Buscar'}</Button>
				<Button size="sm" variant="outline" onclick={saveReorder} disabled={reorderSaving || !coleccion.productos?.length}>{reorderSaving ? 'Guardando…' : 'Guardar orden'}</Button>
			</div>

			{#if searchResults.length}
				<div class="border divide-y bg-background">
					{#each searchResults as prod (prod.id)}
						<div class="flex items-center justify-between gap-2 p-2">
							<div class="min-w-0">
								<div class="font-medium text-sm truncate">{prod.titulo}</div>
								<div class="font-mono text-xs text-muted-foreground truncate">{prod.slug} · ${Number(prod.precio).toFixed(2)}</div>
							</div>
							<Button size="sm" disabled={addingId === prod.id} onclick={() => addProduct(prod.id)}>{addingId === prod.id ? 'Agregando…' : 'Agregar'}</Button>
						</div>
					{/each}
				</div>
			{/if}

			{#if !coleccion.productos || coleccion.productos.length === 0}
				<div class="border border-dashed p-6 text-center text-sm text-muted-foreground">
					Sin productos en esta colección. Usá el buscador arriba para agregar productos (producto debe existir y no estar eliminado).
				</div>
			{:else}
				<div class="overflow-auto border">
					<table class="w-full text-sm">
						<thead class="bg-muted">
							<tr class="text-left font-oswald text-xs tracking-wide">
								<th class="px-2 py-2 w-10">#</th>
								<th class="px-2 py-2">Producto</th>
								<th class="px-2 py-2">Precio</th>
								<th class="px-2 py-2">Orden</th>
								<th class="px-2 py-2">Acciones</th>
							</tr>
						</thead>
						<tbody>
							{#each coleccion.productos as prod, idx (prod.id)}
								<tr class="border-t hover:bg-muted/50">
									<td class="px-2 py-2 text-xs">{idx + 1}</td>
									<td class="px-2 py-2">
										<div class="font-medium truncate max-w-[220px]">{prod.titulo}</div>
										<div class="font-mono text-xs text-muted-foreground">{prod.slug}</div>
									</td>
									<td class="px-2 py-2 text-xs">${Number(prod.precio).toFixed(2)}</td>
									<td class="px-2 py-2 text-xs">{prod.orden ?? idx}</td>
									<td class="px-2 py-2 flex flex-wrap gap-1">
										<button onclick={() => moveUp(idx)} disabled={idx === 0} class="border px-1.5 py-1 text-xs hover:bg-accent disabled:opacity-50">↑</button>
										<button onclick={() => moveDown(idx)} disabled={idx === coleccion.productos.length - 1} class="border px-1.5 py-1 text-xs hover:bg-accent disabled:opacity-50">↓</button>
										<a href="/productos/{prod.id}" class="border px-2 py-1 text-xs hover:bg-accent">Ver</a>
										<button onclick={() => removeProduct(prod.id)} class="border px-2 py-1 text-xs hover:bg-accent text-destructive">Quitar</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				<p class="text-xs text-muted-foreground">Tip: usá ↑↓ para reordenar y luego “Guardar orden” (PATCH reorder con product_ids en orden deseado).</p>
			{/if}
		</Card>
	{/if}
</div>
