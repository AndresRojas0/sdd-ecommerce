<script>
	let { orientation = 'horizontal', class: klass = '' } = $props();
</script>

<div
	class={orientation === 'horizontal' ? 'h-px w-full bg-border ' + klass : 'w-px h-full bg-border ' + klass}
></div>
