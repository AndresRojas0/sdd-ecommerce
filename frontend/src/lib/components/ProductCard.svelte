<script>
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import CategoryBadge from '$lib/components/CategoryBadge.svelte';
	import StarRating from '$lib/components/StarRating.svelte';
	import { tone } from '$lib/stores/tone.js';

	let { product } = $props();

	const PLACEHOLDER_CLASSIC = 'https://placehold.co/400x400/003087/ffd700?text=Punto+App';
	const PLACEHOLDER_GREEN = 'https://placehold.co/400x400/0e7a5a/cbe6d3?text=Punto+App';

	let currentTone = $state('classic');
	tone.subscribe((v) => (currentTone = v));

	let cats = $derived(product.categorias || []);
	let visibleCats = $derived(cats.slice(0, 2));
	let extra = $derived(cats.length > 2 ? cats.length - 2 : 0);
	let img = $derived(product.imagen || (currentTone === 'green' ? PLACEHOLDER_GREEN : PLACEHOLDER_CLASSIC));
</script>

<a href="/producto/{product.slug}" class="block group">
	<Card class="overflow-hidden flex flex-col h-full hover:shadow-offset-navy transition-shadow">
		<div class="aspect-square overflow-hidden bg-muted">
			<img
				src={img}
				alt={product.titulo}
				class="w-full h-full object-cover group-hover:scale-[1.02] transition-transform"
				loading="lazy"
			/>
		</div>
		<div class="p-3 flex flex-col gap-2 flex-1">
			<div class="flex flex-wrap gap-1">
				{#each visibleCats as c}
					<CategoryBadge categoria={c} />
				{/each}
				{#if extra > 0}
					<Badge variant="outline">+{extra}</Badge>
				{/if}
			</div>
			<h3 class="font-oswald font-bold text-sm leading-tight line-clamp-2 min-h-[2.5em]">
				{product.titulo}
			</h3>
			<StarRating promedio={product.calificacion_promedio} cantidad={product.calificacion_cantidad} />
			<div class="flex items-center justify-between mt-auto">
				<span class="text-xs text-muted-foreground">♥ {product.guardados_count ?? 0} guardados</span>
				<span class="font-oswald font-bold text-primary text-lg">${Number(product.precio).toFixed(2)}</span>
			</div>
		</div>
	</Card>
</a>
