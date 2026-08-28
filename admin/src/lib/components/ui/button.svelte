<script>
	import { cn } from '$lib/utils/cn.js';
	let { variant = 'default', size = 'default', class: klass = '', children, ...rest } = $props();
	const base =
		'inline-flex items-center justify-center font-oswald font-bold tracking-wide border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 disabled:pointer-events-none';
	const variants = {
		default: 'bg-primary text-primary-foreground hover:bg-primary/90 border-transparent shadow-offset-navy',
		secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/90 border-transparent shadow-offset-orange',
		destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90 border-transparent',
		outline: 'border-input bg-background hover:bg-accent hover:text-accent-foreground',
		ghost: 'hover:bg-accent hover:text-accent-foreground border-transparent',
		link: 'underline-offset-4 hover:underline text-primary border-transparent'
	};
	const sizes = {
		default: 'h-10 px-4 py-2 text-[15px]',
		sm: 'h-8 px-3 text-sm',
		lg: 'h-11 px-8 text-[19px]',
		icon: 'h-10 w-10'
	};
</script>

<button class={cn(base, variants[variant], sizes[size], klass)} {...rest}>
	{@render children?.()}
</button>
