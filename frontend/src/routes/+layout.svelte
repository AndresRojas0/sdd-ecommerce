<script>
	import '../app.css';
	import '@fontsource/oswald/700.css';
	import '@fontsource/roboto-condensed/400.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user, fetchMe, logout } from '$lib/stores/auth.js';
	import { cartCount, fetchCart } from '$lib/stores/cart.js';
	import DropdownMenu from '$lib/components/ui/dropdown-menu.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import CartSheet from '$lib/components/CartSheet.svelte';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let { children } = $props();
	let dropdownOpen = $state(false);
	let cartOpen = $state(false);

	onMount(async () => {
		await fetchMe();
		// fetch cart if logged
		if ($user) await fetchCart();
	});

	// refetch cart when user changes
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
</script>

<svelte:head>
	<title>Punto App</title>
</svelte:head>

<header class="sticky top-0 z-40 bg-primary text-primary-foreground border-b-4 border-[#e85d04]">
	<nav class="max-w-[1280px] mx-auto flex items-center justify-between gap-4 px-4 py-3">
		<a href="/" class="font-oswald font-bold text-xl tracking-wide flex items-center gap-2">
			<span class="bg-secondary text-secondary-foreground px-2 py-1">PUNTO</span>
			<span>APP</span>
		</a>

		<div class="flex items-center gap-2 md:gap-4">
			{#if $user}
				<a href="/mis-pedidos" class="hidden md:inline text-sm font-oswald hover:underline">Mis Pedidos</a>
				<a href="/mis-favoritos" class="hidden md:inline text-sm font-oswald hover:underline">Mis Favoritos</a>
			{/if}

			<button
				onclick={openCart}
				class="relative p-2 hover:bg-white/10"
				aria-label="Carrito"
			>
				<span class="text-xl">🛒</span>
				{#if $user && $cartCount > 0}
					<span
						class="absolute -top-1 -right-1 bg-secondary text-secondary-foreground text-xs font-bold px-1.5 py-0.5 min-w-[18px] text-center"
						>{$cartCount}</span
					>
				{/if}
			</button>

			{#if $user}
				<DropdownMenu bind:open={dropdownOpen}>
					{#snippet trigger()}
						<span
							class="inline-flex items-center gap-2 bg-white text-primary px-3 py-1 font-oswald text-sm"
							>{$user.display_name || $user.email}</span
						>
					{/snippet}
					<div class="flex flex-col">
						<span class="px-3 py-2 text-sm text-muted-foreground border-b">{$user.email}</span>
						<a href="/mis-pedidos" class="px-3 py-2 text-sm hover:bg-accent" onclick={() => (dropdownOpen = false)}
							>Mis pedidos</a
						>
						<a href="/mis-favoritos" class="px-3 py-2 text-sm hover:bg-accent" onclick={() => (dropdownOpen = false)}
							>Mis favoritos</a
						>
						<button onclick={handleLogout} class="text-left px-3 py-2 text-sm hover:bg-accent text-destructive"
							>Cerrar sesión</button
						>
					</div>
				</DropdownMenu>
			{:else}
				<a
					href="/login"
					class="bg-secondary text-secondary-foreground px-4 py-2 font-oswald font-bold text-sm shadow-offset-orange hover:brightness-95"
					>Ingresar</a
				>
			{/if}
		</div>
	</nav>
</header>

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
