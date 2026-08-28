<script>
		import { page } from '$app/state';
	import { api } from '$lib/api/client.js';
	import CategoryBadge from '$lib/components/CategoryBadge.svelte';
	import StarRating from '$lib/components/StarRating.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import { user } from '$lib/stores/auth.js';
	import { addToCart } from '$lib/stores/cart.js';
	import { goto } from '$app/navigation';
	import { get } from 'svelte/store';

	let slug = $derived(page.params.slug);
	let product = $state(null);
	let loading = $state(true);
	let error = $state(null);
	let cantidad = $state(1);
	let favLoading = $state(false);
	let cartLoading = $state(false);
	let msg = $state(null);
	let cantidadError = $state(null);

	const PLACEHOLDER = 'https://placehold.co/400x400/003087/ffd700?text=Punto+App';

	// Determine origen param: if referrer includes search, mark busqueda
	function getOrigen() {
		if (typeof document === 'undefined') return 'directa';
		const ref = document.referrer;
		if (ref && ref.includes('?')) return 'busqueda';
		// also check if we came via home with query: use sessionStorage flag
		try {
			if (sessionStorage.getItem('lastSearch')) return 'busqueda';
		} catch {}
		return 'directa';
	}

	async function load() {
		loading = true;
		error = null;
		try {
			const data = await api.get(`/products/${slug}`);
			product = data;
			// record visit (non-blocking)
			try {
				const origen = getOrigen();
				await api.post(`/products/${product.id}/visits`, {}, { origen });
			} catch {}
		} catch (e) {
			if (e.status === 404) error = 'Producto no encontrado';
			else error = e.message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		// reload when slug changes
		if (slug) load();
	});

	async function handleAddCart() {
		cantidadError = null;
		if (!get(user)) {
			await goto('/login');
			return;
		}
		if (Number(cantidad) <= 0) {
			cantidadError = 'Cantidad debe ser > 0';
			return;
		}
		cartLoading = true;
		msg = null;
		try {
			await addToCart(product.id, Number(cantidad));
			msg = 'Agregado al carrito';
		} catch (e) {
			msg = e.message;
		} finally {
			cartLoading = false;
		}
	}

	async function handleFav() {
		if (!get(user)) {
			await goto('/login');
			return;
		}
		favLoading = true;
		msg = null;
		try {
			await api.post(`/favorites/${product.id}`, {});
			msg = 'Guardado en favoritos ♥';
			product = { ...product, guardados_count: (product.guardados_count || 0) + 1 };
		} catch (e) {
			// toggle: try delete if already exists
			if (e.message?.includes('Ya en favoritos') || e.status === 409) {
				try {
					await api.delete(`/favorites/${product.id}`);
					msg = 'Quitado de favoritos';
					product = { ...product, guardados_count: Math.max(0, (product.guardados_count || 1) - 1) };
				} catch (e2) {
					msg = e2.message;
				}
			} else {
				msg = e.message;
			}
		} finally {
			favLoading = false;
		}
	}

	function handleShare() {
		navigator.clipboard.writeText(window.location.href);
		msg = 'Link copiado al portapapeles';
		setTimeout(() => (msg = null), 2000);
	}
</script>

<svelte:head>
	<title>{product ? product.titulo + ' — Punto App' : 'Producto — Punto App'}</title>
</svelte:head>

<div class="max-w-[1100px] mx-auto px-4 py-8">
	{#if loading}
		<div class="grid md:grid-cols-2 gap-8">
			<Skeleton class="aspect-square w-full" />
			<div class="flex flex-col gap-3">
				<Skeleton class="h-8 w-3/4" />
				<Skeleton class="h-4 w-1/2" />
				<Skeleton class="h-20 w-full" />
			</div>
		</div>
	{:else if error}
		<Alert variant="destructive"><p>{error}</p></Alert>
		<div class="mt-4"><Button onclick={() => goto('/')}>Volver al catálogo</Button></div>
	{:else if product}
		<div class="grid md:grid-cols-2 gap-8">
			<div class="border shadow-offset-black bg-card p-2">
				<img
					src={product.imagen || PLACEHOLDER}
					alt={product.titulo}
					class="w-full aspect-square object-cover"
				/>
			</div>
			<div class="flex flex-col gap-4">
				<div class="flex flex-wrap gap-2">
					{#each product.categorias || [] as c}
						<CategoryBadge categoria={c} />
					{/each}
				</div>
				<h1 class="font-oswald font-bold text-2xl md:text-3xl leading-tight">{product.titulo}</h1>
				<StarRating promedio={product.calificacion_promedio} cantidad={product.calificacion_cantidad} />
				<div class="flex gap-4 text-sm text-muted-foreground">
					<span>👁 {product.visitas_count ?? 0} visitas</span>
					<span>♥ {product.guardados_count ?? 0} guardados</span>
				</div>
				<div class="font-oswald font-bold text-2xl text-primary">
					${Number(product.precio).toFixed(2)}
					{#if product.unidad_venta}
						<span class="text-sm font-roboto font-normal text-muted-foreground">/ {product.unidad_venta.simbolo}</span>
					{/if}
				</div>
				{#if msg}
					<Alert>{msg}</Alert>
				{/if}
				{#if product.descripcion}
					<p class="text-sm leading-relaxed">{product.descripcion}</p>
				{/if}
				{#if product.componentes_incluidos}
					<div>
						<h3 class="font-oswald font-bold text-sm">Componentes incluidos</h3>
						<p class="text-sm text-muted-foreground">{product.componentes_incluidos}</p>
					</div>
				{/if}
				{#if product.datos_tecnicos && Object.keys(product.datos_tecnicos).length}
					<div>
						<h3 class="font-oswald font-bold text-sm mb-2">Datos técnicos</h3>
						<table class="w-full text-sm border">
							<tbody>
								{#each Object.entries(product.datos_tecnicos) as [k, v]}
									<tr class="border-b">
										<td class="p-2 font-bold bg-muted w-1/3">{k}</td>
										<td class="p-2">{v}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}

				<div class="flex items-center gap-3 pt-2">
					<label class="flex items-center gap-2 text-sm">
						Cantidad
						<input
							type="number"
							min="0.01"
							step="0.01"
							bind:value={cantidad}
							class="border px-2 py-1 w-20"
						/>
					</label>
					{#if cantidadError}
						<span class="text-xs text-destructive">{cantidadError}</span>
					{/if}
				</div>

				<div class="flex flex-wrap gap-2">
					<Button onclick={handleAddCart} disabled={cartLoading}>
						{cartLoading ? 'Agregando…' : 'Agregar al carrito'}
					</Button>
					<Button variant="outline" onclick={handleFav} disabled={favLoading}>
						♥ Favorito
					</Button>
					<Button variant="ghost" onclick={handleShare}>Compartir</Button>
				</div>
			</div>
		</div>
	{/if}
</div>
