<script>
	import Badge from '$lib/components/ui/badge.svelte';

	let { categoria } = $props();

	function luminance(hex) {
		if (!hex || !hex.startsWith('#')) return 0;
		const r = parseInt(hex.slice(1, 3), 16) / 255;
		const g = parseInt(hex.slice(3, 5), 16) / 255;
		const b = parseInt(hex.slice(5, 7), 16) / 255;
		const a = [r, g, b].map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)));
		return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2];
	}

	let bg = $derived(categoria?.color || '#003087');
	let lum = $derived(luminance(bg));
	let textColor = $derived(lum > 0.5 ? '#1a1f3a' : '#ffffff');
</script>

<Badge style="background:{bg}; color:{textColor}; border-color:{bg}">{categoria.nombre}</Badge>
