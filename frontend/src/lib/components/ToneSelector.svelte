<script>
	import { tone } from '$lib/stores/tone.js';

	let current = $state('classic');

	tone.subscribe((v) => (current = v));

	function select(t) {
		tone.setTone(t);
	}
</script>

<div class="flex items-center gap-2" aria-label="Selector de tonalidad">
	<span class="text-xs font-oswald font-bold uppercase tracking-wide opacity-70">Tono:</span>
	{#each Object.entries(tone.TONES) as [key, info]}
		<button
			onclick={() => select(key)}
			class="flex items-center gap-1.5 px-2.5 py-1 border-2 font-oswald text-xs font-bold uppercase tracking-wide transition"
			class:bg-white={current === key}
			class:text-[#003087]={current === key}
			class:border-[#ffd700]={current === key}
			class:bg-transparent={current !== key}
			class:text-white={current !== key}
			class:border-white={current !== key}
			aria-pressed={current === key}
			title={info.label}
		>
			<span class="flex gap-0.5">
				{#each info.colors as c}
					<span class="w-3 h-3 border border-black/10" style="background:{c}"></span>
				{/each}
			</span>
			{info.label}
		</button>
	{/each}
</div>
