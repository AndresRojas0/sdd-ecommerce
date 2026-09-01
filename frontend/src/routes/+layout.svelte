<script>
	import '../app.css';
	import '@fontsource/oswald/700.css';
	import '@fontsource/roboto-condensed/400.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { user, fetchMe, logout } from '$lib/stores/auth.js';
	import { cartCount, fetchCart } from '$lib/stores/cart.js';
	import { api } from '$lib/api/client.js';
	import DropdownMenu from '$lib/components/ui/dropdown-menu.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import CartSheet from '$lib/components/CartSheet.svelte';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let { children } = $props();
	let dropdownOpen = $state(false);
	let cartOpen = $state(false);
	let searchQuery = $state('');
	let categorias = $state([]);
	let searchDebounce;

	onMount(async () => {
		await fetchMe();
		if ($user) await fetchCart();
		// Cargar categorías para la nav
		try {
			const data = await api.get('/categorias');
			categorias = Array.isArray(data) ? data : data.items || [];
		} catch {}
		// Sincronizar búsqueda con URL
		const urlQ = $page.url.searchParams.get('q');
		if (urlQ) searchQuery = urlQ;
	});

	$effect(() => {
		if ($user) fetchCart();
	});

	async function handleLogout() {
		await logout();
		dropdownOpen = false;
		await goto('/');
	}
	function openCart() {
		if (!$user) {
			goto('/login');
			return;
		}
		cartOpen = true;
	}
	function handleSearch(e) {
		e.preventDefault();
		const q = searchQuery.trim();
		if (q.length === 0) {
			goto('/productos', { replaceState: true });
		} else {
			goto(`/productos?q=${encodeURIComponent(q)}`, { replaceState: true });
		}
	}
	function onSearchInput(e) {
		searchQuery = e.target.value;
		clearTimeout(searchDebounce);
		searchDebounce = setTimeout(() => {
			const q = searchQuery.trim();
			if (q.length >= 2 || q.length === 0) {
				if (q.length === 0) goto('/productos', { replaceState: true });
				else goto(`/productos?q=${encodeURIComponent(q)}`, { replaceState: true });
			}
		}, 300);
	}
	function clearSearch() {
		searchQuery = '';
		goto('/productos', { replaceState: true });
	}
</script>

<svelte:head>
	<title>Punto App</title>
</svelte:head>

<header class="site-header sticky top-0 z-40" role="banner">
	<!-- Promo ticker -->
	<div class="promo-ticker" aria-label="Promociones">
		<div class="promo-ticker__inner">
			★ ¡NO PAGUES DE MÁS EN PUNTO APP! <span class="promo-ticker__sep">|</span>
			ENVÍO GRATIS EN PEDIDOS SELECCIONADOS <span class="promo-ticker__sep">|</span>
			ASESORAMIENTO EXPERTO EN CADA COMPRA <span class="promo-ticker__sep">|</span>
			TODOS LOS PRECIOS INCLUYEN IVA <span class="promo-ticker__sep">|</span>
			HERRAMIENTAS • MATERIALES • REPUESTOS <span class="promo-ticker__sep">|</span>
			★ ¡EL PUNTO DE PARTIDA DE TU PRÓXIMO PROYECTO! <span class="promo-ticker__sep">|</span>
			ENVÍO GRATIS EN PEDIDOS SELECCIONADOS <span class="promo-ticker__sep">|</span>
			ASESORAMIENTO EXPERTO EN CADA COMPRA
		</div>
	</div>

	<!-- Header main: logo + buscador + acciones -->
	<div class="header-main-wrap bg-[#003087] border-b-4 border-[#ffd700]">
		<div class="max-w-[1280px] mx-auto px-3 py-2.5 flex items-center gap-3">
			<a href="/" class="flex items-center gap-2 shrink-0" aria-label="Punto App Inicio">
				<div class="bg-white border-[3px] border-[#ffd700] px-2 py-1 flex flex-col items-center leading-none">
					<span class="font-oswald font-bold text-[1.6rem] leading-none text-[#003087] tracking-tight">PUN<span class="text-[#cc0000]">T</span>O</span>
					<span class="font-roboto text-[0.55rem] text-[#003087] uppercase tracking-widest">Ferretería</span>
				</div>
				<span class="hidden sm:inline font-oswald font-bold text-[#ffd700] text-lg tracking-wide">PUNTO APP</span>
			</a>

			<form class="flex-1 flex max-w-[520px] mx-auto" role="search" onsubmit={handleSearch}>
				<input
					type="search"
					bind:value={searchQuery}
					oninput={onSearchInput}
					placeholder="Buscar productos, SKU, datos técnicos..."
					aria-label="Buscar productos"
					class="flex-1 px-3 py-2 border-[3px] border-[#ffd700] border-r-0 text-sm bg-white text-[#1a1f3a] outline-none focus:bg-[#fffef0] placeholder:text-[#888]"
				/>
				<button
					type="submit"
					aria-label="Buscar"
					class="bg-[#ffd700] border-[3px] border-[#ffd700] px-4 font-oswald font-bold text-sm text-[#001d5e] uppercase tracking-wide hover:brightness-95 flex items-center gap-1"
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
					<span class="hidden sm:inline">Buscar</span>
				</button>
				{#if searchQuery}
					<button type="button" onclick={clearSearch} class="ml-1 px-2 text-white/80 hover:text-white text-sm" title="Limpiar búsqueda">✕</button>
				{/if}
			</form>

			<div class="flex items-center gap-1.5 shrink-0">
				{#if $user}
					<a href="/mis-favoritos" class="hidden md:flex flex-col items-center gap-0.5 border-2 border-[#ffd700] text-[#ffd700] px-2.5 py-1 font-oswald font-bold text-[0.65rem] uppercase tracking-wide hover:bg-[#ffd700] hover:text-[#001d5e] no-underline">
						<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
						Favs
					</a>
				{/if}

				<button
					onclick={openCart}
					class="relative flex flex-col items-center gap-0.5 border-2 border-[#ffd700] text-[#ffd700] px-2.5 py-1 font-oswald font-bold text-[0.65rem] uppercase tracking-wide hover:bg-[#ffd700] hover:text-[#001d5e]"
					aria-label="Carrito"
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
					Carrito
					{#if $user && $cartCount > 0}
						<span class="absolute -top-1.5 -right-1.5 bg-[#cc0000] text-white text-[0.6rem] font-bold w-[18px] h-[18px] rounded-full flex items-center justify-center border-2 border-[#003087]">{$cartCount}</span>
					{/if}
				</button>

				{#if $user}
					<DropdownMenu bind:open={dropdownOpen}>
						{#snippet trigger()}
							<span class="hidden sm:inline-flex items-center gap-1.5 bg-white text-[#003087] px-2.5 py-1 font-oswald text-xs border-2 border-[#ffd700]">{$user.display_name || $user.email}</span>
						{/snippet}
						<div class="flex flex-col">
							<span class="px-3 py-2 text-sm text-muted-foreground border-b">{$user.email}</span>
							<a href="/mis-pedidos" class="px-3 py-2 text-sm hover:bg-accent" onclick={() => (dropdownOpen = false)}>Mis pedidos</a>
							<a href="/mis-favoritos" class="px-3 py-2 text-sm hover:bg-accent" onclick={() => (dropdownOpen = false)}>Mis favoritos</a>
							<button onclick={handleLogout} class="text-left px-3 py-2 text-sm hover:bg-accent text-destructive">Cerrar sesión</button>
						</div>
					</DropdownMenu>
				{:else}
					<a href="/login" class="flex flex-col items-center gap-0.5 border-2 border-[#ffd700] text-[#ffd700] px-3 py-1 font-oswald font-bold text-[0.65rem] uppercase tracking-wide hover:bg-[#ffd700] hover:text-[#001d5e] no-underline">
						<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
						Ingresar
					</a>
				{/if}
			</div>
		</div>
	</div>

	<!-- Nav categorías -->
	<nav class="nav-bar bg-[#e85d04] border-t-2 border-[#c44b00]" aria-label="Categorías">
		<div class="max-w-[1280px] mx-auto px-3">
			<div class="flex items-stretch overflow-x-auto scrollbar-none gap-0" style="scrollbar-width:none">
				<a href="/productos" class="shrink-0 bg-[#001d5e] text-[#ffd700] px-3 py-2 font-oswald font-bold text-xs uppercase tracking-wide flex items-center gap-1.5 border-r-2 border-[#c44b00] no-underline hover:brightness-110">
					<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
					Todas
				</a>
				{#each categorias as cat}
					<a href="/productos?categoria={cat.slug}" class="shrink-0 flex items-center px-3 py-2 text-white font-oswald font-semibold text-xs uppercase tracking-wide whitespace-nowrap border-r border-white/20 hover:bg-[#c44b00] no-underline">
						{cat.nombre}
					</a>
				{/each}
			</div>
		</div>
	</nav>
</header>

<style>
	.promo-ticker {
		background: #ffd700;
		color: #001d5e;
		font-family: 'Oswald', sans-serif;
		font-weight: 700;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		padding: 5px 0;
		overflow: hidden;
		border-bottom: 2px solid #e85d04;
	}
	.promo-ticker__inner {
		display: inline-block;
		white-space: nowrap;
		animation: ticker 30s linear infinite;
	}
	@keyframes ticker {
		0% { transform: translateX(100vw); }
		100% { transform: translateX(-100%); }
	}
	.promo-ticker__sep { margin: 0 2rem; color: #e85d04; }
	.scrollbar-none::-webkit-scrollbar { display: none; }
</style>

<CartSheet bind:open={cartOpen} />

<main class="min-h-[70vh]">
	{@render children()}
</main>

<footer class="bg-[#003087] text-white mt-12 border-t-4 border-[#e85d04]">
	<div class="max-w-[1280px] mx-auto px-4 py-6 flex flex-col md:flex-row items-center justify-between gap-4">
		<div class="flex items-center gap-2 font-oswald font-bold">
			<span class="bg-[#ffd700] text-[#003087] px-2 py-1">PUNTO</span> APP
			<span class="text-xs font-roboto font-normal opacity-70 ml-2">MVP — ferretería</span>
		</div>
		<div class="flex items-center gap-4 text-sm">
			<a href="/" class="hover:underline">Catálogo</a>
			<a href="/carrito" class="hover:underline">Carrito</a>
			<ThemeToggle />
		</div>
	</div>
</footer>
