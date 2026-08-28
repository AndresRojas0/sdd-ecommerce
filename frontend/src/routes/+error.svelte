<script>
	import { page } from '$app/stores';
	import Button from '$lib/components/ui/button.svelte';

	let status = $derived($page.status);
	let is404 = $derived(status === 404);
</script>

<div class="min-h-[60vh] flex flex-col items-center justify-center gap-4 bg-[#003087] text-white px-4 py-16 text-center">
	<div class="text-7xl">🔩</div>
	<h1 class="font-oswald font-bold text-3xl md:text-4xl">
		{#if is404}
			404 — Esta pieza no está en el taller
		{:else}
			{status} — Algo salió mal
		{/if}
	</h1>
	<p class="text-[#f0f0f0] text-sm max-w-[480px]">
		La ruta que buscaste no existe o el producto ya no está disponible. Volvé al catálogo y seguí
		buscando tu próximo proyecto.
	</p>
	<a href="/" class="bg-[#ffd700] text-[#1a1f3a] px-6 py-3 font-oswald font-bold shadow-offset-orange hover:brightness-95">
		Volver al inicio
	</a>
</div>
