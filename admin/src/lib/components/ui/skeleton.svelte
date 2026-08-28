<script>
	import { cn } from '$lib/utils/cn.js';
	let { class: klass = '', ...rest } = $props();
</script>

<div class={cn('animate-pulse bg-muted', klass)} {...rest}></div>
