<script>
	import { cn } from '$lib/utils/cn.js';
	let { variant = 'default', class: klass = '', style = '', children, ...rest } = $props();
	const variants = {
		default: 'bg-primary text-primary-foreground',
		secondary: 'bg-secondary text-secondary-foreground',
		destructive: 'bg-destructive text-destructive-foreground',
		outline: 'border text-foreground'
	};
</script>

<span
	class={cn(
		'inline-flex items-center px-2.5 py-0.5 text-xs font-oswald font-bold tracking-wide border',
		variants[variant],
		klass
	)}
	{style}
	{...rest}
>
	{@render children?.()}
</span>
