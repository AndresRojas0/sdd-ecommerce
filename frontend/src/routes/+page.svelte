<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import InfiniteGrid from '$lib/components/InfiniteGrid.svelte';

	let products = $state([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state(null);
	let sort = $state('relevance');
	let offset = $state(0);
	const limit = 12;

	let hasMore = $derived(products.length < total);

	async function fetchProducts(reset = false) {
		if (reset) {
			offset = 0;
			products = [];
		}
		loading = true;
		error = null;
		try {
			const params = { limit, offset, sort };
			const urlQ = $page.url.searchParams.get('q');
			const urlCat = $page.url.searchParams.get('categoria');
			if (urlQ) params.q = urlQ;
			if (urlCat) params.categoria = urlCat;
			const data = await api.get('/products', params);
			total = data.total;
			if (reset) products = data.items;
			else products = [...products, ...data.items];
			offset = products.length;
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function onLoadMore() {
		if (!loading && hasMore) fetchProducts(false);
	}

	onMount(() => fetchProducts(true));

	$effect(() => {
		// Re-fetch when URL query changes (búsqueda desde header)
		void $page.url.searchParams.get('q');
		void $page.url.searchParams.get('categoria');
		fetchProducts(true);
	});
</script>

<svelte:head>
	<title>Punto App — Catálogo</title>
</svelte:head>

<!-- Hero (sin buscador, ahora en header) -->
<section class="bg-[#003087] text-white">
	<div class="max-w-[1280px] mx-auto px-4 py-10 md:py-12 grid md:grid-cols-2 gap-8 items-center">
		<div class="flex flex-col gap-3">
			<h1 class="font-oswald font-bold text-[32px] md:text-[56px] leading-none tracking-wide">
				El punto de partida<br />
				<span class="text-[#ffd700]">de tu próximo proyecto.</span>
			</h1>
			<p class="font-roboto text-sm md:text-[16px] text-[#f0f0f0] max-w-[520px]">
				Herramientas, materiales y repuestos. Buscá por nombre o dato técnico, filtrá por categoría y
				etiqueta, y encontralo al toque.
			</p>
		</div>
		<div class="bg-white p-4 border shadow-offset-orange flex flex-col gap-3">
			<p class="font-oswald font-bold text-[#003087] text-sm uppercase tracking-wide">Ordenar por</p>
			<label class="flex items-center gap-2 text-sm text-[#1a1f3a]">
				<select
					bind:value={sort}
					onchange={() => fetchProducts(true)}
					class="border-2 border-[#003087] px-3 py-2 bg-white font-roboto flex-1"
				>
					<option value="relevance">Relevancia</option>
					<option value="mas_reciente">Más reciente</option>
					<option value="precio_asc">Precio ↑</option>
					<option value="precio_desc">Precio ↓</option>
					<option value="a_z">A-Z</option>
					<option value="z_a">Z-A</option>
				</select>
			</label>
			<p class="text-xs text-[#666]">Usá el buscador del header para filtrar por nombre, categoría o etiqueta.</p>
		</div>
	</div>
</section>

<section class="max-w-[1280px] mx-auto px-4 py-8">
	<InfiniteGrid {products} {loading} {hasMore} {error} {onLoadMore} />
</section>
