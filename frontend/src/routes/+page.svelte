<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import SearchBar from '$lib/components/SearchBar.svelte';
	import InfiniteGrid from '$lib/components/InfiniteGrid.svelte';

	let products = $state([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state(null);
	let q = $state('');
	let categoria = $state(null);
	let tags = $state([]);
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
			if (q) params.q = q;
			if (categoria) params.categoria = categoria;
			if (tags.length) params.tags = tags.join(',');
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

	function onSearch(obj) {
		q = obj.q || '';
		categoria = obj.categoria;
		tags = obj.tags || [];
		fetchProducts(true);
	}

	function onLoadMore() {
		if (!loading && hasMore) fetchProducts(false);
	}

	onMount(() => fetchProducts(true));
</script>

<svelte:head>
	<title>Punto App — Catálogo</title>
</svelte:head>

<!-- Hero -->
<section class="bg-[#003087] text-white">
	<div class="max-w-[1280px] mx-auto px-4 py-10 md:py-12 grid md:grid-cols-2 gap-8 items-center">
		<div class="flex flex-col gap-3">
			<h1 class="font-oswald font-bold text-[32px] md:text-[48px] leading-none tracking-wide">
				El punto de partida<br />
				<span class="text-[#ffd700]">de tu próximo proyecto.</span>
			</h1>
			<p class="font-roboto text-sm md:text-[14px] text-[#f0f0f0] max-w-[520px]">
				Herramientas, materiales y repuestos. Buscá por nombre o dato técnico, filtrá por categoría y
				etiqueta, y encontralo al toque.
			</p>
		</div>
		<div class="bg-white p-4 border shadow-offset-orange">
			<SearchBar bind:value={q} bind:categoria bind:tags {onSearch} />
			<div class="mt-3 flex gap-2 text-xs">
				<label class="flex items-center gap-1 text-[#1a1f3a]">
					Orden:
					<select
						bind:value={sort}
						onchange={() => fetchProducts(true)}
						class="border px-2 py-1 bg-white"
					>
						<option value="relevance">Relevancia</option>
						<option value="mas_reciente">Más reciente</option>
						<option value="precio_asc">Precio ↑</option>
						<option value="precio_desc">Precio ↓</option>
						<option value="a_z">A-Z</option>
						<option value="z_a">Z-A</option>
					</select>
				</label>
			</div>
		</div>
	</div>
</section>

<section class="max-w-[1280px] mx-auto px-4 py-8">
	<InfiniteGrid {products} {loading} {hasMore} {error} {onLoadMore} />
</section>
