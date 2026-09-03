<script>
	import '../app.css';
	import '@fontsource/oswald/700.css';
	import '@fontsource/roboto-condensed/400.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { user, fetchMe, logout, authError } from '$lib/stores/auth.js';
	import DropdownMenu from '$lib/components/ui/dropdown-menu.svelte';
	import Button from '$lib/components/ui/button.svelte';

	let { children } = $props();
	let dropdownOpen = $state(false);
	let checkingAuth = $state(true);
	let mobileNavOpen = $state(false);

	const navLinks = [
		{ href: '/', label: 'Dashboard', icon: '📊' },
		{ href: '/usuarios', label: 'Usuarios', icon: '👥' },
		{ href: '/vendedores', label: 'Vendedores', icon: '🏷️' },
		{ href: '/productos', label: 'Productos', icon: '📦' },
		{ href: '/categorias', label: 'Categorías', icon: '🗂️' },
		{ href: '/colecciones', label: 'Colecciones', icon: '✨' },
		{ href: '/pedidos', label: 'Pedidos', icon: '🧾' },
		{ href: '/ordenes', label: 'Órdenes', icon: '📑' },
		{ href: '/stock', label: 'Stock', icon: '📊' }
	];

	let currentPath = $derived($page.url.pathname);
	let isLoginPage = $derived(currentPath === '/login');

	onMount(async () => {
		if (isLoginPage) {
			checkingAuth = false;
			return;
		}
		const me = await fetchMe();
		if (!me) {
			await goto('/login');
		}
		checkingAuth = false;
	});

	$effect(() => {
		// if already on login and user becomes set, redirect
		if ($user && isLoginPage) {
			goto('/');
		}
	});

	async function handleLogout() {
		await logout();
		dropdownOpen = false;
		await goto('/login');
	}

	function isActive(href) {
		if (href === '/') return currentPath === '/';
		return currentPath.startsWith(href);
	}
</script>

<svelte:head>
	<title>Punto App — Admin</title>
	<script>
		// theme init before paint
		try {
			const t = localStorage.getItem('theme');
			const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
			if (t === 'dark' || (!t && prefersDark)) document.documentElement.classList.add('dark');
		} catch {}
	</script>
</svelte:head>

{#if isLoginPage}
	{@render children()}
{:else if checkingAuth}
	<div class="min-h-screen flex items-center justify-center bg-[#1a1f3a] text-white">
		<div class="animate-pulse font-oswald text-xl">Cargando…</div>
	</div>
{:else if !$user}
	<div class="min-h-screen flex flex-col items-center justify-center gap-4 bg-[#1a1f3a] text-white p-6">
		<p class="font-oswald text-xl">Acceso denegado</p>
		<p class="text-sm text-white/70">Se requiere rol administrador o vendedor.</p>
		<Button variant="secondary" onclick={() => goto('/login')}>Ir a login</Button>
	</div>
{:else}
	<div class="min-h-screen flex flex-col bg-background">
		<header class="sticky top-0 z-40 bg-[#1a1f3a] text-white border-b-4 border-[#e85d04]">
			<nav class="max-w-[1400px] mx-auto flex items-center justify-between gap-4 px-4 py-3">
				<div class="flex items-center gap-6">
					<a href="/" class="font-oswald font-bold text-lg tracking-wide flex items-center gap-2">
						<span class="bg-[#ffd700] text-[#1a1f3a] px-2 py-1 text-sm">PUNTO</span>
						<span>APP — Admin</span>
						<span class="ml-2 text-xs font-roboto font-normal opacity-60 hidden md:inline">{$user.role}</span>
					</a>
					<div class="hidden lg:flex items-center gap-1">
						{#each navLinks as link}
							<a
								href={link.href}
								class="px-3 py-1.5 text-xs font-oswald font-bold tracking-wide border-b-2 transition-colors
								{isActive(link.href)
									? 'border-[#e85d04] bg-white/10'
									: 'border-transparent hover:bg-white/10'}"
							>
								{link.label}
							</a>
						{/each}
					</div>
				</div>

				<div class="flex items-center gap-2">
					<button
						class="lg:hidden p-2 border border-white/20"
						onclick={() => (mobileNavOpen = !mobileNavOpen)}
						aria-label="Menu"
					>
						☰
					</button>

					<DropdownMenu bind:open={dropdownOpen}>
						{#snippet trigger()}
							<span
								class="inline-flex items-center gap-2 bg-white text-[#1a1f3a] px-3 py-1 font-oswald text-sm"
							>
								{$user.display_name || $user.email}
								<span class="hidden md:inline text-xs bg-[#e85d04] text-white px-1.5 py-0.5">{$user.role}</span>
							</span>
						{/snippet}
						<div class="flex flex-col">
							<span class="px-3 py-2 text-sm text-muted-foreground border-b">{$user.email}</span>
							<span class="px-3 py-2 text-xs text-muted-foreground">Rol: {$user.role}</span>
							<button onclick={handleLogout} class="text-left px-3 py-2 text-sm hover:bg-accent text-destructive"
								>Cerrar sesión</button
							>
						</div>
					</DropdownMenu>
				</div>
			</nav>
			{#if mobileNavOpen}
				<div class="lg:hidden border-t border-white/10 bg-[#1a1f3a] px-4 py-3 flex flex-col gap-1">
					{#each navLinks as link}
						<a
							href={link.href}
							onclick={() => (mobileNavOpen = false)}
							class="px-3 py-2 text-sm font-oswald font-bold {isActive(link.href)
								? 'bg-white text-[#1a1f3a]'
								: 'text-white hover:bg-white/10'}"
						>
							{link.label}
						</a>
					{/each}
				</div>
			{/if}
		</header>

		<main class="flex-1 max-w-[1400px] w-full mx-auto px-4 py-6">
			{@render children()}
		</main>

		<footer class="bg-[#1a1f3a] text-white border-t-4 border-[#e85d04] mt-auto">
			<div class="max-w-[1400px] mx-auto px-4 py-4 flex flex-col md:flex-row items-center justify-between gap-2 text-sm">
				<div class="flex items-center gap-2 font-oswald font-bold">
					<span class="bg-[#ffd700] text-[#1a1f3a] px-2 py-1">PUNTO</span> APP Admin
					<span class="text-xs font-roboto font-normal opacity-60 ml-2">panel interno</span>
				</div>
				<span class="text-xs opacity-60">Punto App — ferretería · Admin SPA</span>
			</div>
		</footer>
	</div>
{/if}
