<script>
	import { cn } from '$lib/utils/cn.js';
	let { variant = 'default', class: klass = '', children, ...rest } = $props();
	const variants = {
		default: 'bg-background text-foreground border',
		destructive: 'border-destructive/50 text-destructive bg-destructive/10'
	};
</script>

<div role="alert" class={cn('relative w-full border p-4', variants[variant], klass)} {...rest}>
	{@render children?.()}
</div>
