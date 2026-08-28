<script>
	let { promedio = 0, cantidad = 0 } = $props();

	let full = $derived(Math.floor(Number(promedio) || 0));
	let fraction = $derived((Number(promedio) || 0) % 1);
	let pct = $derived(Math.round(fraction * 100));
</script>

<div class="flex items-center gap-1">
	<div class="flex">
		{#each Array(5) as _, i}
			<div class="relative w-4 h-4 leading-none">
				<!-- empty star -->
				<span class="absolute inset-0 text-[#cccccc] text-[16px] leading-none">★</span>
				{#if i < full}
					<span class="absolute inset-0 text-[#ffd700] text-[16px] leading-none overflow-hidden">★</span>
				{:else if i === full && pct > 0}
					<span
						class="absolute inset-0 text-[#ffd700] text-[16px] leading-none overflow-hidden"
						style="width:{pct}%">★</span
					>
				{/if}
			</div>
		{/each}
	</div>
	{#if cantidad !== undefined}
		<span class="text-xs text-muted-foreground font-roboto">({cantidad})</span>
	{/if}
</div>
