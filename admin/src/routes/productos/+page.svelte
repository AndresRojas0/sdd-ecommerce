<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import Input from '$lib/components/ui/input.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';

	let products = $state([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state(null);
	let q = $state('');
	let categoria = $state('');
	let sort = $state('');
	let limit = 20;
	let offset = $state(0);
	let categorias = $state([]);

	async function fetchCategorias() {
		try {
			categorias = await api.get('/categorias');
		} catch {}
	}

	async function fetchProducts() {
		loading = true;
		error = null;
		try {
			const params = { limit, offset, include_hidden: true };
			if (q) params.q = q;
			if (categoria) params.categoria = categoria;
			if (sort) params.sort = sort;
			const data = await api.get('/products', params);
			products = data.items;
			total = data.total;
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	async function toggleVisibility(p) {
		const nuevo = p.estado_publicacion === 'publicado' ? 'oculto' : 'publicado';
		try {
			await api.patch(`/products/${p.id}/visibility`, null, { estado: nuevo });
			await fetchProducts();
		} catch (e) {
			alert('Error: ' + e.message);
		}
	}

	async function deleteProduct(p) {
		if (!confirm(`¿Eliminar (baja lógica RN-32) "${p.titulo}"?`)) return;
		try {
			await api.delete(`/products/${p.id}`);
			await fetchProducts();
		} catch (e) {
			alert('Error: ' + e.message);
		}
	}

	function nextPage() {
		if (offset + limit < total) {
			offset += limit;
			fetchProducts();
		}
	}
	function prevPage() {
		if (offset > 0) {
			offset = Math.max(0, offset - limit);
			fetchProducts();
		}
	}

	function onSearch() {
		offset = 0;
		fetchProducts();
	}

	onMount(() => {
		fetchCategorias();
		fetchProducts();
	});
</script>

<svelte:head>
	<title>Productos — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
		<div>
			<h1 class="font-oswald font-bold text-xl">Productos</h1>
			<p class="text-xs text-muted-foreground">UC-AD06..AD11 · RN-31 ocultar, RN-32 baja lógica, RN-24 alta · incluye ocultos</p>
		</div>
		<a href="/productos/nuevo" class="bg-primary text-primary-foreground px-4 py-2 text-sm font-oswald font-bold border shadow-offset-navy text-center">+ Nuevo producto</a>
	</div>

	<Card class="p-3 flex flex-col gap-3">
		<div class="flex flex-col md:flex-row gap-2">
			<Input bind:value={q} placeholder="Buscar por título o datos técnicos…" class="md:max-w-sm" />
			<select bind:value={categoria} class="border bg-background px-3 py-2 text-sm h-10">
				<option value="">Todas las categorías</option>
				{#each categorias as c}
					<option value={c.slug}>{c.nombre}</option>
				{/each}
			</select>
			<select bind:value={sort} class="border bg-background px-3 py-2 text-sm h-10">
				<option value="">Relevancia</option>
				<option value="mas_reciente">Más reciente</option>
				<option value="precio_asc">Precio ↑</option>
				<option value="precio_desc">Precio ↓</option>
				<option value="a_z">A-Z</option>
				<option value="z_a">Z-A</option>
			</select>
			<Button size="sm" onclick={onSearch}>Buscar</Button>
			<Button variant="outline" size="sm" onclick={fetchProducts}>Actualizar</Button>
		</div>
		<span class="text-xs text-muted-foreground">Total: {total} · Mostrando {products.length} · include_hidden=true (staff ve todo)</span>
	</Card>

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
							<th class="px-3 py-2">Título</th>
							<th class="px-3 py-2">Slug</th>
							<th class="px-3 py-2">Precio</th>
							<th class="px-3 py-2">Estado</th>
							<th class="px-3 py-2">Categorías</th>
							<th class="px-3 py-2">Visitas</th>
							<th class="px-3 py-2">Acciones</th>
						</tr>
					</thead>
					<tbody>
						{#each products as p (p.id)}
							<tr class="border-t hover:bg-muted/50">
								<td class="px-3 py-2 font-medium max-w-[200px] truncate">{p.titulo}</td>
								<td class="px-3 py-2 font-mono text-xs">{p.slug}</td>
								<td class="px-3 py-2">${Number(p.precio).toFixed(2)}</td>
								<td class="px-3 py-2">
									<Badge variant={p.deleted_at ? 'destructive' : p.estado_publicacion === 'publicado' ? 'secondary' : 'outline'}>
										{p.deleted_at ? 'eliminado' : p.estado_publicacion}
									</Badge>
								</td>
								<td class="px-3 py-2">
									<div class="flex flex-wrap gap-1">
										{#each p.categorias.slice(0, 2) as c}
											<span class="px-1.5 py-0.5 text-xs border" style="background:{c.color}20; border-color:{c.color}">{c.nombre}</span>
										{/each}
										{#if p.categorias.length > 2}<span class="text-xs">+{p.categorias.length - 2}</span>{/if}
									</div>
								</td>
								<td class="px-3 py-2 text-xs">{p.visitas_count} · ♥{p.guardados_count}</td>
								<td class="px-3 py-2 flex flex-wrap gap-1">
									<a href="/productos/{p.id}" class="border px-2 py-1 text-xs hover:bg-accent">Ver</a>
									<a href="/productos/{p.id}/editar" class="border px-2 py-1 text-xs hover:bg-accent">Editar</a>
									<button onclick={() => toggleVisibility(p)} disabled={!!p.deleted_at} class="border px-2 py-1 text-xs hover:bg-accent disabled:opacity-50">
										{p.estado_publicacion === 'publicado' ? 'Ocultar' : 'Publicar'}
									</button>
									<button onclick={() => deleteProduct(p)} class="border px-2 py-1 text-xs hover:bg-accent text-destructive">Eliminar</button>
								</td>
							</tr>
						{/each}
						{#if products.length === 0}
							<tr><td colspan="7" class="px-3 py-6 text-center text-muted-foreground">Sin productos</td></tr>
						{/if}
					</tbody>
				</table>
			</div>
			<div class="flex items-center justify-between p-3 border-t bg-muted/20">
				<span class="text-xs">Página {Math.floor(offset / limit) + 1} de {Math.ceil(total / limit) || 1}</span>
				<div class="flex gap-2">
					<Button variant="outline" size="sm" onclick={prevPage} disabled={offset === 0}>Anterior</Button>
					<Button variant="outline" size="sm" onclick={nextPage} disabled={offset + limit >= total}>Siguiente</Button>
				</div>
			</div>
		</Card>
	{/if}
</div>
