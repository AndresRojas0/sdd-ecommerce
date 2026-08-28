<script>
	import { cn } from '$lib/utils/cn.js';
	let { class: klass = '', value = $bindable(''), type = 'text', ...rest } = $props();
</script>

<input
	{type}
	bind:value
	class={cn(
		'flex h-10 w-full border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
		klass
	)}
	{...rest}
/>
