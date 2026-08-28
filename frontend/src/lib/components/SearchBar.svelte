<script>
	import Input from '$lib/components/ui/input.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Button from '$lib/components/ui/button.svelte';

	let { value = $bindable(''), categoria = $bindable(null), tags = $bindable([]), onSearch } = $props();

	let inputVal = $state(value);
	let timer;

	function debouncedSearch(v) {
		clearTimeout(timer);
		timer = setTimeout(() => {
			if (v.length === 0 || v.length >= 2) {
				value = v;
				onSearch?.({ q: v, categoria, tags });
			}
		}, 300);
	}

	function onInput(e) {
		inputVal = e.target.value;
		debouncedSearch(inputVal);
	}

	function clearCategoria() {
		categoria = null;
		onSearch?.({ q: value, categoria, tags });
	}
	function clearTag(t) {
		tags = tags.filter((x) => x !== t);
		onSearch?.({ q: value, categoria, tags });
	}
	function clearAll() {
		inputVal = '';
		value = '';
		categoria = null;
		tags = [];
		onSearch?.({ q: '', categoria: null, tags: [] });
	}

	$effect(() => {
		// sync external value
		if (value !== inputVal) inputVal = value;
	});
</script>

<div class="flex flex-col gap-2 w-full">
	<Input placeholder="Buscá por nombre o dato técnico…" value={inputVal} oninput={onInput} class="bg-white text-[#1a1f3a]" />
	{#if categoria || tags.length > 0 || value}
		<div class="flex flex-wrap items-center gap-2">
			{#if categoria}
				<Badge class="gap-1 bg-secondary text-secondary-foreground">
					{categoria}
					<button onclick={clearCategoria} aria-label="Quitar filtro categoría" class="ml-1 font-bold">✕</button>
				</Badge>
			{/if}
			{#each tags as t}
				<Badge class="gap-1">
					{t}
					<button onclick={() => clearTag(t)} aria-label="Quitar tag" class="ml-1">✕</button>
				</Badge>
			{/each}
			<Button variant="ghost" size="sm" onclick={clearAll}>Limpiar filtros</Button>
		</div>
	{/if}
</div>
