<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client.js';
	import Input from '$lib/components/ui/input.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Alert from '$lib/components/ui/alert.svelte';

	let titulo = $state('');
	let slug = $state('');
	let descripcion = $state('');
	let componentes = $state('');
	let datosTecnicos = $state('{}');
	let precio = $state('10.00');
	let imagen = $state('');
	let unidad_id = $state('');
	let categoria_ids = $state([]);
	let etiqueta_ids_str = $state('');
	let loading = $state(false);
	let error = $state(null);
	let success = $state(null);

	let unidades = $state([]);
	let categorias = $state([]);
	let etiquetas = $state([]);
	let autocompleteResults = $state([]);
	let etiquetaQuery = $state('');

	function slugify(s) {
		return s
			.toLowerCase()
			.trim()
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/^-|-$/g, '');
	}

	$effect(() => {
		if (titulo && !slug) slug = slugify(titulo);
	});

	async function fetchRefs() {
		try {
			unidades = await api.get('/unidades-medida');
			categorias = await api.get('/categorias');
			etiquetas = await api.get('/etiquetas');
			if (unidades.length) unidad_id = unidades[0].id;
		} catch (e) {
			error = e.message;
		}
	}

	async function onEtiquetaInput(e) {
		etiquetaQuery = e.target.value;
		if (etiquetaQuery.length < 1) {
			autocompleteResults = [];
			return;
		}
		try {
			autocompleteResults = await api.get('/etiquetas/autocomplete', { q: etiquetaQuery });
		} catch {
			autocompleteResults = [];
		}
	}

	function addEtiqueta(id) {
		const current = etiqueta_ids_str
			.split(',')
			.map((s) => s.trim())
			.filter(Boolean);
		if (!current.includes(id)) current.push(id);
		etiqueta_ids_str = current.join(', ');
		autocompleteResults = [];
		etiquetaQuery = '';
	}

	async function submit(e) {
		e.preventDefault();
		loading = true;
		error = null;
		success = null;
		let parsedDatos = {};
		try {
			parsedDatos = datosTecnicos ? JSON.parse(datosTecnicos) : {};
		} catch {
			error = 'datos_tecnicos debe ser JSON válido';
			loading = false;
			return;
		}
		const etiqueta_ids = etiqueta_ids_str
			.split(',')
			.map((s) => s.trim())
			.filter(Boolean);
		// resolve etiqueta slugs to ids if needed
		const resolvedIds = [];
		for (const v of etiqueta_ids) {
			// if it's already UUID
			if (v.match(/^[0-9a-f-]{36}$/i)) resolvedIds.push(v);
			else {
				// try find by slug or nombre
				const found = etiquetas.find((et) => et.slug === v || et.nombre === v);
				if (found) resolvedIds.push(found.id);
				else {
					// try create? For now create new etiqueta via POST
					try {
						const newTag = await api.post('/etiquetas', { nombre: v, slug: slugify(v) });
						resolvedIds.push(newTag.id);
					} catch (err) {
						error = 'Error creando etiqueta ' + v + ': ' + err.message;
						loading = false;
						return;
					}
				}
			}
		}
		const payload = {
			titulo,
			slug: slugify(slug || titulo),
			descripcion: descripcion || null,
			componentes_incluidos: componentes || null,
			datos_tecnicos: parsedDatos,
			precio: precio,
			imagen: imagen || null,
			unidad_venta_id: unidad_id,
			categoria_ids,
			etiqueta_ids: resolvedIds
		};
		try {
			const created = await api.post('/products', payload);
			success = 'Producto creado: ' + created.titulo;
			setTimeout(() => goto('/productos/' + created.id), 800);
		} catch (err) {
			const d = err.data?.detail;
			error = typeof d === 'string' ? d : d ? JSON.stringify(d) : err.message;
		} finally {
			loading = false;
		}
	}

	onMount(fetchRefs);
</script>

<svelte:head>
	<title>Nuevo producto — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4 max-w-3xl">
	<a href="/productos" class="text-sm underline">← Volver a productos</a>
	<h1 class="font-oswald font-bold text-xl">Nuevo producto</h1>
	<p class="text-xs text-muted-foreground">UC-V01 / UC-AD08 · RN-24 · Slug auto desde título, unidad y categorías requeridas</p>

	{#if error}<Alert variant="destructive"><p class="text-sm whitespace-pre-wrap">{error}</p></Alert>{/if}
	{#if success}<Alert><p class="text-sm">{success}</p></Alert>{/if}

	<Card class="p-4">
		<form onsubmit={submit} class="flex flex-col gap-4">
			<div class="grid md:grid-cols-2 gap-3">
				<label class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Título *</span>
					<Input bind:value={titulo} required placeholder="Ej: Tornillo acero inox 5x30" />
				</label>
				<label class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Slug *</span>
					<Input bind:value={slug} required placeholder="auto" />
					<span class="text-xs text-muted-foreground">se genera desde título</span>
				</label>
			</div>

			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Descripción</span>
				<textarea bind:value={descripcion} rows="3" class="border bg-background px-3 py-2 text-sm" placeholder="Descripción larga"></textarea>
			</label>

			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Componentes incluidos</span>
				<Input bind:value={componentes} placeholder="Ej: 100 unidades + llave" />
			</label>

			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Datos técnicos (JSON)</span>
				<textarea bind:value={datosTecnicos} rows="3" class="border bg-background px-3 py-2 text-sm font-mono text-xs" placeholder="JSON"></textarea>
			</label>

			<div class="grid md:grid-cols-3 gap-3">
				<label class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Precio *</span>
					<Input bind:value={precio} type="number" step="0.01" required />
				</label>
				<label class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Unidad venta *</span>
					<select bind:value={unidad_id} class="border bg-background px-3 py-2 text-sm h-10">
						{#each unidades as u}
							<option value={u.id}>{u.nombre} ({u.simbolo})</option>
						{/each}
					</select>
				</label>
				<label class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Imagen URL</span>
					<Input bind:value={imagen} placeholder="https://..." />
				</label>
			</div>

			<div class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Categorías * (al menos una, RN-01)</span>
				<div class="flex flex-wrap gap-2 border p-2 bg-muted/20">
					{#each categorias as c}
						<label class="flex items-center gap-1 text-xs border px-2 py-1 bg-background cursor-pointer">
							<input type="checkbox" value={c.id} onchange={(e) => {
								if (e.target.checked) categoria_ids = [...categoria_ids, c.id];
								else categoria_ids = categoria_ids.filter(id => id !== c.id);
							}} checked={categoria_ids.includes(c.id)} />
							{c.nombre}
						</label>
					{/each}
				</div>
			</div>

			<div class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Etiquetas (IDs o slugs comma, RN-02/RN-03)</span>
				<Input bind:value={etiqueta_ids_str} placeholder="ej: acero, tornillos o UUIDs comma" />
				<div class="flex gap-2">
					<Input value={etiquetaQuery} oninput={onEtiquetaInput} placeholder="autocomplete q…" class="max-w-xs" />
				</div>
				{#if autocompleteResults.length}
					<div class="flex flex-wrap gap-1">
						{#each autocompleteResults as et}
							<button type="button" onclick={() => addEtiqueta(et.id)} class="border px-2 py-1 text-xs hover:bg-accent">{et.nombre} ({et.slug})</button>
						{/each}
					</div>
				{/if}
				<div class="flex flex-wrap gap-1 mt-1">
					{#each etiquetas.slice(0, 8) as et}
						<button type="button" onclick={() => addEtiqueta(et.id)} class="text-xs border px-1.5 py-0.5 hover:bg-accent">{et.nombre}</button>
					{/each}
				</div>
			</div>

			<Button type="submit" disabled={loading}>{loading ? 'Creando…' : 'Crear producto'}</Button>
		</form>
	</Card>
</div>
