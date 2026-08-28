<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import { user } from '$lib/stores/auth.js';
	import { goto } from '$app/navigation';
	import ProductCard from '$lib/components/ProductCard.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Button from '$lib/components/ui/button.svelte';

	let items = $state([]);
	let loading = $state(true);
	let error = $state(null);

	onMount(async () => {
		if (!$user) {
			await goto('/login');
			return;
		}
		try {
			const favs = await api.get('/favorites');
			// favs: [{producto: {id, titulo, slug, precio, imagen}}]
			// Need to hydrate to full product for ProductCard
			const hydrated = [];
			for (const f of favs) {
				try {
					if (f.producto?.slug) {
						const prod = await api.get(`/products/${f.producto.slug}`);
						hydrated.push(prod);
					} else if (f.product_id) {
						const prod = await api.get(`/products/${f.product_id}`);
						hydrated.push(prod);
					}
				} catch {}
			}
			items = hydrated;
		} catch (e) {
			if (e.status === 401) await goto('/login');
			else error = e.message;
		} finally {
			loading = false;
		}
	});
</script>

<div class="max-w-[1280px] mx-auto px-4 py-8">
	<h1 class="font-oswald font-bold text-2xl mb-6">Mis Favoritos</h1>

	{#if loading}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			{#each Array(4) as _}
				<Skeleton class="aspect-square w-full h-[280px]" />
			{/each}
		</div>
	{:else if error}
		<Alert variant="destructive"><p>{error}</p></Alert>
	{:else if items.length === 0}
		<div class="text-center py-16 flex flex-col gap-4 items-center">
			<p class="text-muted-foreground">Aún no guardaste favoritos.</p>
			<Button onclick={() => goto('/')}>Explorar catálogo</Button>
		</div>
	{:else}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			{#each items as p (p.id)}
				<ProductCard product={p} />
			{/each}
		</div>
	{/if}
</div>
