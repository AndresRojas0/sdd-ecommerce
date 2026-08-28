<script>
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import ProductCard from '$lib/components/ProductCard.svelte';

	let { products = [], loading = false, hasMore = false, onLoadMore, error = null } = $props();

	let sentinel = $state(null);
	let observer;

	$effect(() => {
		if (!sentinel) return;
		observer?.disconnect();
		observer = new IntersectionObserver(
			(entries) => {
				if (entries[0].isIntersecting && hasMore && !loading) onLoadMore?.();
			},
			{ rootMargin: '200px' }
		);
		observer.observe(sentinel);
		return () => observer?.disconnect();
	});
</script>

{#if error}
	<Alert variant="destructive" class="mb-4">
		<p>{error}</p>
		<Button variant="outline" size="sm" class="mt-2" onclick={() => onLoadMore?.()}>Reintentar</Button>
	</Alert>
{/if}

{#if products.length === 0 && !loading}
	<div class="flex flex-col items-center justify-center py-16 gap-4 text-center">
		<div class="text-6xl">🔧</div>
		<p class="font-oswald font-bold text-xl">No encontramos nada para tu búsqueda</p>
		<p class="text-sm text-muted-foreground">Probá limpiando filtros o cambiando el término.</p>
	</div>
{:else}
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
		{#each products as p (p.id)}
			<ProductCard product={p} />
		{/each}
		{#if loading}
			{#each Array(4) as _}
				<div class="border p-3 flex flex-col gap-2">
					<Skeleton class="aspect-square w-full" />
					<Skeleton class="h-4 w-3/4" />
					<Skeleton class="h-4 w-1/2" />
					<Skeleton class="h-6 w-1/3 ml-auto" />
				</div>
			{/each}
		{/if}
	</div>
	<div bind:this={sentinel} class="h-4"></div>
{/if}
