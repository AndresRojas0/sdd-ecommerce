<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Button from '$lib/components/ui/button.svelte';

	let product = $state(null);
	let loading = $state(true);
	let error = $state(null);
	let stats = $state(null);
	let id = $derived($page.params.id);

	async function fetchProduct() {
		loading = true;
		error = null;
		try {
			product = await api.get(`/products/${id}`);
			try {
				stats = await api.get(`/products/${id}/stats`);
			} catch {}
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	onMount(fetchProduct);
</script>

<svelte:head>
	<title>{product?.titulo ?? 'Producto'} — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<a href="/productos" class="text-sm underline">← Volver a productos</a>

	{#if loading}
		<Skeleton class="h-64 w-full" />
	{:else if error}
		<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
	{:else if product}
		<Card class="p-4 flex flex-col gap-4">
			<div class="flex flex-col md:flex-row justify-between gap-3">
				<div>
					<h1 class="font-oswald font-bold text-xl">{product.titulo}</h1>
					<p class="font-mono text-xs text-muted-foreground">{product.slug} · {product.id}</p>
				</div>
				<div class="flex flex-wrap gap-2">
					<Badge variant={product.deleted_at ? 'destructive' : product.estado_publicacion === 'publicado' ? 'secondary' : 'outline'}>{product.deleted_at ? 'eliminado' : product.estado_publicacion}</Badge>
					<Badge>${Number(product.precio).toFixed(2)}</Badge>
					<a href="/productos/{product.id}/editar" class="border px-3 py-1 text-xs bg-primary text-primary-foreground">Editar</a>
				</div>
			</div>

			{#if product.imagen}
				<img src={product.imagen} alt={product.titulo} class="max-h-64 object-contain border bg-muted" />
			{/if}

			<div class="grid md:grid-cols-2 gap-4 text-sm">
				<div>
					<h3 class="font-oswald font-bold">Descripción</h3>
					<p class="text-muted-foreground">{product.descripcion || '—'}</p>
					<h3 class="font-oswald font-bold mt-3">Componentes</h3>
					<p class="text-muted-foreground">{product.componentes_incluidos || '—'}</p>
					<h3 class="font-oswald font-bold mt-3">Datos técnicos</h3>
					<pre class="bg-muted p-2 text-xs overflow-auto">{JSON.stringify(product.datos_tecnicos, null, 2)}</pre>
				</div>
				<div>
					<h3 class="font-oswald font-bold">Categorías</h3>
					<div class="flex flex-wrap gap-1 mt-1">
						{#each product.categorias as c}
							<span class="px-2 py-1 text-xs border" style="background:{c.color}20">{c.nombre} ({c.slug})</span>
						{/each}
					</div>
					<h3 class="font-oswald font-bold mt-3">Etiquetas</h3>
					<div class="flex flex-wrap gap-1 mt-1">
						{#each product.etiquetas as t}
							<Badge variant="outline">{t.nombre}</Badge>
						{/each}
						{#if product.etiquetas.length === 0}<span class="text-xs text-muted-foreground">Sin etiquetas</span>{/if}
					</div>
					<h3 class="font-oswald font-bold mt-3">Unidad</h3>
					<p class="text-xs">{product.unidad_venta?.nombre} ({product.unidad_venta?.simbolo})</p>
					<p class="text-xs text-muted-foreground mt-2">Creado: {new Date(product.created_at).toLocaleString()} · Actualizado: {new Date(product.updated_at).toLocaleString()}</p>
				</div>
			</div>

			{#if stats}
				<div class="border-t pt-3">
					<h3 class="font-oswald font-bold text-sm">Estadísticas (UC-AD11 · RN-08, RN-09, RN-21, RN-30)</h3>
					<div class="grid grid-cols-2 md:grid-cols-5 gap-2 mt-2 text-xs">
						<div class="border p-2 text-center"><div class="font-bold text-lg">{stats.visitas_count}</div><div class="text-muted-foreground">visitas</div></div>
						<div class="border p-2 text-center"><div class="font-bold text-lg">{stats.guardados_count}</div><div class="text-muted-foreground">guardados</div></div>
						<div class="border p-2 text-center"><div class="font-bold text-lg">{stats.busquedas_count}</div><div class="text-muted-foreground">búsquedas (relevancia)</div></div>
						<div class="border p-2 text-center"><div class="font-bold text-lg">{Number(stats.calificacion_promedio).toFixed(2)}</div><div class="text-muted-foreground">promedio ★</div></div>
						<div class="border p-2 text-center"><div class="font-bold text-lg">{stats.calificacion_cantidad}</div><div class="text-muted-foreground">calificaciones</div></div>
					</div>
				</div>
			{/if}
		</Card>
	{/if}
</div>
