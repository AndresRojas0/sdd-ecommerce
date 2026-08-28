<script>
	import { cn } from '$lib/utils/cn.js';
	let { class: klass = '', children, ...rest } = $props();
</script>

<div class="w-full overflow-auto border">
	<table class={cn('w-full text-sm', klass)} {...rest}>
		{@render children?.()}
	</table>
</div>
