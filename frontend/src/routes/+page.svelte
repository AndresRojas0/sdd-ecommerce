<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client.js';
	import ProductCard from '$lib/components/ProductCard.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';

	let categorias = $state([]);
	let nuevos = $state([]);
	let destacados = $state([]);
	let loadingCats = $state(true);
	let loadingNuevos = $state(true);
	let loadingDestacados = $state(true);
	let errorNuevos = $state(null);
	let errorDestacados = $state(null);
	let errorCats = $state(null);

	function isWithin30Days(dateStr) {
		if (!dateStr) return false;
		const d = new Date(dateStr);
		const now = Date.now();
		return now - d.getTime() <= 30 * 24 * 60 * 60 * 1000;
	}

	onMount(async () => {
		try {
			const data = await api.get('/categorias');
			categorias = Array.isArray(data) ? data : data.items || [];
		} catch (e) {
			errorCats = e.message;
		} finally {
			loadingCats = false;
		}
		try {
			const data = await api.get('/products', { sort: 'mas_reciente', limit: 8 });
			const items = data.items || [];
			const filtered = items.filter((p) => isWithin30Days(p.created_at));
			nuevos = filtered.length > 0 ? filtered.slice(0, 8) : items.slice(0, 8);
		} catch (e) {
			errorNuevos = e.message;
		} finally {
			loadingNuevos = false;
		}
		try {
			const data = await api.get('/products', { sort: 'relevance', limit: 8 });
			destacados = data.items || [];
		} catch (e) {
			errorDestacados = e.message;
		} finally {
			loadingDestacados = false;
		}
	});

	function goCategoria(cat) {
		goto(`/productos?categoria=${encodeURIComponent(cat.slug)}`);
	}

	const catIcons = {
		bazar: '🧹',
		'calefacción': '🔥',
		calefaccion: '🔥',
		cerrajería: '🔑',
		cerrajeria: '🔑',
		construcción: '🧱',
		construccion: '🧱',
		corte: '✂️',
		'desbaste y pulido': '🪚',
		electricidad: '⚡',
		fontanería: '🚿',
		fontaneria: '🚿',
		iluminación: '💡',
		iluminacion: '💡',
		gas: '🔧',
		herramientas: '🔨',
		'materias primas': '🪵',
		pintura: '🎨',
		plomería: '🚰',
		plomeria: '🚰',
		refrigeración: '❄️',
		refrigeracion: '❄️',
		sanitarios: '🚽',
		'suministros seguridad': '🦺'
	};
	function catIcon(cat) {
		const key = cat.slug?.toLowerCase();
		if (catIcons[key]) return catIcons[key];
		const nameKey = cat.nombre?.toLowerCase();
		if (catIcons[nameKey]) return catIcons[nameKey];
		return (cat.nombre || cat.slug || '?').charAt(0).toUpperCase();
	}
</script>

<svelte:head>
	<title>Punto App — Inicio</title>
</svelte:head>

<!-- Hero -->
<section class="hero" aria-label="Hero banner">
	<div class="container">
		<div class="hero__inner">
			<div class="hero__content">
				<span class="hero__eyebrow">Ferretería · Herramientas · Repuestos</span>
				<h1 class="hero__title">El punto de partida <em>de tu próximo proyecto.</em></h1>
				<p class="hero__body">
					Herramientas, materiales y repuestos. Buscá por nombre o dato técnico, filtrá por categoría y encontralo al toque.
				</p>
				<div class="hero__actions">
					<a href="/productos" class="btn btn-primary">BUSCAR YA →!</a>
					<a href="/productos?nuevos=true" class="btn btn-secondary">NUEVOS PRODUCTOS</a>
				</div>
			</div>
			<div class="hero__aside">
				<div class="hammer-box" aria-label="Promoción martillo">
					<div class="hammer-box__title">Punto App</div>
					<div class="hammer-box__word">Hammer</div>
					<div class="hammer-box__sub">Miles de</div>
					<div class="hammer-box__exclaim">¡Precios!</div>
				</div>
			</div>
		</div>
	</div>
</section>

<!-- Promo strip -->
<div class="promo-strip" role="complementary" aria-label="Promesas de la tienda">
	<div class="container">
		<div class="promo-strip__inner">
			<span>ENVÍO GRATIS • ASESORAMIENTO EXPERTO • TODOS LOS PRECIOS INCLUYEN IVA</span>
		</div>
	</div>
</div>

<!-- COMPRAR POR CATEGORÍA -->
<section class="section" aria-labelledby="cat-heading">
	<div class="container">
		<div class="section-hdr">
			<div class="section-hdr__bar" id="cat-heading">COMPRAR POR CATEGORÍA</div>
			<a href="/productos" class="section-hdr__link">Ver todo →</a>
		</div>
		{#if loadingCats}
			<div class="category-grid">
				{#each Array(8) as _}
					<Skeleton class="h-[86px] w-full" />
				{/each}
			</div>
		{:else if errorCats}
			<p class="text-sm text-destructive">{errorCats}</p>
		{:else if categorias.length === 0}
			<p class="text-sm text-muted-foreground">No hay categorías disponibles.</p>
		{:else}
			<div class="category-grid">
				{#each categorias as cat (cat.id || cat.slug)}
					<button type="button" class="category-card" onclick={() => goCategoria(cat)} aria-label="Ver {cat.nombre}">
						<span class="category-card__icon">{catIcon(cat)}</span>
						<span class="category-card__name">{cat.nombre}</span>
					</button>
				{/each}
			</div>
		{/if}
	</div>
</section>

<!-- Nuevos productos -->
<section class="section" aria-labelledby="new-heading">
	<div class="container">
		<div class="section-hdr">
			<div class="section-hdr__bar section-hdr__bar--green" id="new-heading">NUEVOS PRODUCTOS</div>
			<a href="/productos?nuevos=true" class="section-hdr__link">Ver todos →</a>
		</div>
		{#if loadingNuevos}
			<div class="product-grid">
				{#each Array(4) as _}
					<div class="border p-3 flex flex-col gap-2">
						<Skeleton class="aspect-square w-full" />
						<Skeleton class="h-4 w-3/4" />
						<Skeleton class="h-4 w-1/2" />
					</div>
				{/each}
			</div>
		{:else if errorNuevos}
			<p class="text-sm text-destructive">{errorNuevos}</p>
		{:else if nuevos.length === 0}
			<p class="text-sm text-muted-foreground">Aún no hay productos nuevos.</p>
		{:else}
			<div class="product-grid">
				{#each nuevos as p (p.id)}
					<ProductCard product={p} />
				{/each}
			</div>
		{/if}
	</div>
</section>

<!-- Guarantee banner -->
<div class="guarantee-banner" role="complementary" aria-label="Garantía de precio">
	<div class="container">
		<div class="guarantee-banner__inner">
			<div class="guarantee-banner__text">
				<h2>Garantía de precio ¡Imbatible!</h2>
				<p>
					Si encontrás el mismo producto más barato en otro lado dentro de los 7 días de tu compra,
					no solo igualamos el precio sino que <strong>te devolvemos un 20% extra de la diferencia.</strong>
					<br /><small>* Sujeto a condiciones en tienda.</small>
				</p>
			</div>
			<div class="guarantee-banner__percent" aria-label="20 percent extra">
				<div class="num">20%</div>
				<div class="label">de la diferencia</div>
			</div>
		</div>
	</div>
</div>

<!-- Productos destacados -->
<section class="section" aria-labelledby="feat-heading">
	<div class="container">
		<div class="section-hdr">
			<div class="section-hdr__bar section-hdr__bar--orange" id="feat-heading">PRODUCTOS DESTACADOS</div>
			<a href="/productos?sort=relevance" class="section-hdr__link">Ver todos →</a>
		</div>
		{#if loadingDestacados}
			<div class="product-grid">
				{#each Array(4) as _}
					<div class="border p-3 flex flex-col gap-2">
						<Skeleton class="aspect-square w-full" />
						<Skeleton class="h-4 w-3/4" />
						<Skeleton class="h-4 w-1/2" />
					</div>
				{/each}
			</div>
		{:else if errorDestacados}
			<p class="text-sm text-destructive">{errorDestacados}</p>
		{:else if destacados.length === 0}
			<p class="text-sm text-muted-foreground">Aún no hay productos destacados.</p>
		{:else}
			<div class="product-grid">
				{#each destacados as p (p.id)}
					<ProductCard product={p} />
				{/each}
			</div>
		{/if}
	</div>
</section>
