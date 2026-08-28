<script>
	import Button from '$lib/components/ui/button.svelte';
	import { browser } from '$app/environment';

	let isDark = $state(false);

	$effect(() => {
		if (!browser) return;
		isDark = document.documentElement.classList.contains('dark');
	});

	function toggle() {
		isDark = !isDark;
		if (isDark) {
			document.documentElement.classList.add('dark');
			localStorage.setItem('theme', 'dark');
		} else {
			document.documentElement.classList.remove('dark');
			localStorage.setItem('theme', 'light');
		}
	}
</script>

<Button variant="ghost" size="sm" onclick={toggle} aria-label="Cambiar tema">
	{#if isDark}☀️ Claro{:else}🌙 Oscuro{/if}
</Button>
