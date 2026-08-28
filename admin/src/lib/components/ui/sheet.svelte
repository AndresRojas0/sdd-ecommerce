<script>
	import { cn } from '$lib/utils/cn.js';
	let { open = $bindable(false), class: klass = '', children, ...rest } = $props();
	function close() {
		open = false;
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="fixed inset-0 z-50 flex justify-end">
		<div class="absolute inset-0 bg-black/50" onclick={close}></div>
		<div
			class={cn(
				'relative bg-background w-full max-w-sm h-full shadow-lg border-l flex flex-col animate-in slide-in-from-right',
				klass
			)}
			{...rest}
		>
			<button
				onclick={close}
				class="absolute right-3 top-3 p-2 hover:bg-accent"
				aria-label="Cerrar">✕</button
			>
			{@render children?.()}
		</div>
	</div>
{/if}
