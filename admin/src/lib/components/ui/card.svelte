<script>
	import { cn } from '$lib/utils/cn.js';
	let { class: klass = '', children, ...rest } = $props();
</script>

<div class={cn('bg-card text-card-foreground border shadow-offset-black', klass)} {...rest}>
	{@render children?.()}
</div>
