<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import ProductCard from '$lib/components/ProductCard.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Alert from '$lib/components/ui/alert.svelte';

	let categorias = $state([]);
	let products = $state([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state(null);

	let sort = $state('relevance');
	let selectedCats = $state([]);
	let precioMin = $state('');
	let precioMax = $state('');

	let q = $state('');
	let nuevosOnly = $state(false);

	function isWithin30Days(dateStr) {
		if (!dateStr) return false;
		const d = new Date(dateStr);
		return Date.now() - d.getTime() <= 30 * 24 * 60 * 60 * 1000;
	}

	function readInitialFilters() {
		const params = $page.url.searchParams;
		q = params.get('q') || '';
		const catSlug = params.get('categoria');
		if (catSlug) selectedCats = [catSlug];
		else selectedCats = [];
		const nuevosParam = params.get('nuevos');
		nuevosOnly = nuevosParam === 'true' || nuevosParam === '1';
		const sortParam = params.get('sort');
		if (sortParam && ['relevance', 'mas_reciente', 'precio_asc', 'precio_desc', 'a_z', 'z_a'].includes(sortParam)) {
			sort = sortParam;
		}
	}

	async function fetchProducts() {
		loading = true;
		error = null;
		try {
			const allItems = [];
			if (selectedCats.length === 0) {
				const params = { limit: 100, offset: 0, sort };
				if (q) params.q = q;
				const data = await api.get('/products', params);
				let items = data.items || [];
				items = applyClientFilters(items);
				allItems.push(...items);
				total = data.total;
				// If client filtered, total may differ; adjust display
				if (nuevosOnly || precioMin !== '' || precioMax !== '') {
					total = allItems.length;
				}
				products = allItems;
			} else {
				// Multi-select: fetch per category and merge deduped. API supports single categoria param.
				const seen = new Set();
				for (const catSlug of selectedCats) {
					const params = { limit: 100, offset: 0, sort, categoria: catSlug };
					if (q) params.q = q;
					const data = await api.get('/products', params);
					for (const item of data.items || []) {
						if (!seen.has(item.id)) {
							seen.add(item.id);
							allItems.push(item);
						}
					}
				}
				let items = applyClientFilters(allItems);
				// sort client-side when merging multiple categories
				items = sortItems(items, sort);
				products = items;
				total = items.length;
			}
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function sortItems(items, sortVal) {
		const copy = [...items];
		if (sortVal === 'precio_asc') copy.sort((a, b) => Number(a.precio) - Number(b.precio));
		else if (sortVal === 'precio_desc') copy.sort((a, b) => Number(b.precio) - Number(a.precio));
		else if (sortVal === 'mas_reciente') copy.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
		else if (sortVal === 'a_z') copy.sort((a, b) => a.titulo.localeCompare(b.titulo));
		else if (sortVal === 'z_a') copy.sort((a, b) => b.titulo.localeCompare(a.titulo));
		else if (sortVal === 'relevance') copy.sort((a, b) => (b.busquedas_count || 0) - (a.busquedas_count || 0));
		return copy;
	}

	function applyClientFilters(items) {
		let filtered = items;
		if (nuevosOnly) {
			filtered = filtered.filter((p) => isWithin30Days(p.created_at));
		}
		const min = precioMin !== '' ? Number(precioMin) : null;
		const max = precioMax !== '' ? Number(precioMax) : null;
		if (min !== null && !isNaN(min)) {
			filtered = filtered.filter((p) => Number(p.precio) >= min);
		}
		if (max !== null && !isNaN(max)) {
			filtered = filtered.filter((p) => Number(p.precio) <= max);
		}
		return filtered;
	}

	function toggleCat(slug) {
		if (selectedCats.includes(slug)) selectedCats = selectedCats.filter((s) => s !== slug);
		else selectedCats = [...selectedCats, slug];
	}

	function onSortChange(e) {
		sort = e.target.value;
		fetchProducts();
	}

	function aplicarFiltros() {
		fetchProducts();
	}

	function limpiarFiltros() {
		selectedCats = [];
		precioMin = '';
		precioMax = '';
		sort = 'relevance';
		q = '';
		nuevosOnly = false;
		fetchProducts();
	}

	onMount(async () => {
		readInitialFilters();
		try {
			const data = await api.get('/categorias');
			categorias = Array.isArray(data) ? data : data.items || [];
		} catch {}
		await fetchProducts();
	});

	// React to URL changes for q/categoria/nuevos (e.g. header search or category grid nav)
	let prevQ = $state(null);
	let prevCatParam = $state(null);
	let prevNuevos = $state(null);
	let initialized = $state(false);
	$effect(() => {
		const curQ = $page.url.searchParams.get('q') || '';
		const curCat = $page.url.searchParams.get('categoria') || '';
		const curNuevos = $page.url.searchParams.get('nuevos') || '';
		if (!initialized) {
			initialized = true;
			prevQ = curQ;
			prevCatParam = curCat;
			prevNuevos = curNuevos;
			return;
		}
		if (curQ !== prevQ || curCat !== prevCatParam || curNuevos !== prevNuevos) {
			prevQ = curQ;
			prevCatParam = curCat;
			prevNuevos = curNuevos;
			q = curQ;
			nuevosOnly = curNuevos === 'true' || curNuevos === '1';
			if (curCat) selectedCats = [curCat];
			else selectedCats = [];
			fetchProducts();
		}
	});
</script>

<svelte:head>
	<title>Productos — Punto App</title>
</svelte:head>

<div style="background: var(--cream); border-bottom: 2px solid var(--grey);">
	<div class="container">
		<nav class="breadcrumb" aria-label="Breadcrumb">
			<a href="/">Inicio</a>
			<span class="breadcrumb__sep">›</span>
			<span class="breadcrumb__current">Productos</span>
		</nav>
	</div>
</div>

<div class="container" style="padding-top: 16px; padding-bottom: 32px;">
	<div class="divider-bar" style="margin-bottom: 16px;">Productos — Punto App</div>

	<div class="shop-layout">
		<aside class="sidebar" aria-label="Filtros">
			<div class="sidebar__section">
				<div class="sidebar__title">ORDENAR POR</div>
				<div class="sidebar__body">
					<select class="form-select w-full" bind:value={sort} onchange={onSortChange} aria-label="Ordenar por">
						<option value="relevance">Relevancia</option>
						<option value="mas_reciente">Más reciente</option>
						<option value="precio_asc">Precio ↑</option>
						<option value="precio_desc">Precio ↓</option>
						<option value="a_z">A-Z</option>
						<option value="z_a">Z-A</option>
					</select>
				</div>
			</div>

			<div class="sidebar__section">
				<div class="sidebar__title">CATEGORÍAS</div>
				<div class="sidebar__body">
					{#if categorias.length === 0}
						<p class="text-xs text-muted-foreground">Cargando…</p>
					{:else}
						<ul class="filter-list" role="list">
							{#each categorias as cat (cat.id || cat.slug)}
								<li class="filter-item">
									<input
										type="checkbox"
										id="f-{cat.slug}"
										checked={selectedCats.includes(cat.slug)}
										onchange={() => toggleCat(cat.slug)}
									/>
									<label for="f-{cat.slug}">{cat.nombre}</label>
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			</div>

			<div class="sidebar__section">
				<div class="sidebar__title">RANGO PRECIOS</div>
				<div class="sidebar__body">
					<div class="price-range">
						<div class="price-range__inputs">
							<input type="number" placeholder="$ Min" min="0" bind:value={precioMin} aria-label="Precio mínimo" />
							<span class="price-range__sep">—</span>
							<input type="number" placeholder="$ Max" min="0" bind:value={precioMax} aria-label="Precio máximo" />
						</div>
					</div>
				</div>
			</div>

			<div style="padding: 10px 12px; display: flex; flex-direction: column; gap: 8px;">
				<button class="btn btn-primary btn-sm w-full" onclick={aplicarFiltros}>APLICAR FILTROS DE BÚSQUEDA</button>
				<button class="btn btn-blue btn-sm w-full" onclick={limpiarFiltros}>LIMPIAR FILTROS</button>
			</div>
		</aside>

		<div>
			<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
				<div style="font-family:'Oswald',sans-serif;font-size:0.85rem;color:var(--grey-dark);text-transform:uppercase;letter-spacing:0.04em;">
					Mostrando <strong style="color:var(--blue-dark);">{loading ? '…' : products.length}</strong> productos
					{#if total && total !== products.length} de {total}{/if}
				</div>
			</div>

			{#if error}
				<Alert variant="destructive"><p>{error}</p></Alert>
			{:else if loading}
				<div class="product-grid">
					{#each Array(8) as _}
						<div class="border p-3 flex flex-col gap-2">
							<Skeleton class="aspect-square w-full" />
							<Skeleton class="h-4 w-3/4" />
							<Skeleton class="h-4 w-1/2" />
							<Skeleton class="h-6 w-1/3 ml-auto" />
						</div>
					{/each}
				</div>
			{:else if products.length === 0}
				<div style="grid-column:1/-1;text-align:center;padding:48px 24px;background:var(--white);border:2px solid var(--grey);">
					<p style="font-family:'Oswald',sans-serif;color:var(--blue-dark);font-size:1rem;">No encontramos productos con esos filtros.</p>
					<p class="text-sm text-muted-foreground mt-2">Probá limpiando filtros o cambiando la búsqueda.</p>
				</div>
			{:else}
				<div class="product-grid">
					{#each products as p (p.id)}
						<ProductCard product={p} />
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>
