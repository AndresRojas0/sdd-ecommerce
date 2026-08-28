<script>
	import { cn } from '$lib/utils/cn.js';
	let { open = $bindable(false), class: klass = '', children, title = '', ...rest } = $props();
	function close() {
		open = false;
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="fixed inset-0 z-50 flex items-center justify-center">
		<div class="absolute inset-0 bg-black/50" onclick={close}></div>
		<div
			class={cn('relative bg-card border shadow-offset-black w-full max-w-lg max-h-[90vh] overflow-auto p-6', klass)}
			{...rest}
		>
			{#if title}
				<h3 class="font-oswald font-bold text-lg mb-4">{title}</h3>
			{/if}
			<button
				onclick={close}
				class="absolute right-3 top-3 p-1 hover:bg-accent"
				aria-label="Cerrar">✕</button
			>
			{@render children?.()}
		</div>
	</div>
{/if}
