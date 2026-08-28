<script>
	import { cn } from '$lib/utils/cn.js';
	let { open = $bindable(false), trigger, children, class: klass = '' } = $props();
</script>

<div class="relative inline-block text-left">
	<button onclick={() => (open = !open)} class={cn('outline-none', klass)}>
		{@render trigger?.()}
	</button>
	{#if open}
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="fixed inset-0 z-10" onclick={() => (open = false)}></div>
		<div
			class="absolute right-0 z-20 mt-2 w-56 bg-popover border shadow-offset-black p-1"
		>
			{@render children?.()}
		</div>
	{/if}
</div>
