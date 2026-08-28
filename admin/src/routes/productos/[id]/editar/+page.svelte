<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client.js';
	import Input from '$lib/components/ui/input.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';

	let id = $derived($page.params.id);
	let loading = $state(true);
	let saving = $state(false);
	let error = $state(null);
	let success = $state(null);

	let titulo = $state('');
	let slug = $state('');
	let descripcion = $state('');
	let componentes = $state('');
	let datosTecnicos = $state('{}');
	let precio = $state('');
	let imagen = $state('');
	let unidad_id = $state('');
	let categoria_ids = $state([]);
	let etiqueta_ids_str = $state('');

	let unidades = $state([]);
	let categorias = $state([]);
	let etiquetas = $state([]);

	async function fetchAll() {
		loading = true;
		try {
			unidades = await api.get('/unidades-medida');
			categorias = await api.get('/categorias');
			etiquetas = await api.get('/etiquetas');
			const p = await api.get(`/products/${id}`);
			titulo = p.titulo;
			slug = p.slug;
			descripcion = p.descripcion || '';
			componentes = p.componentes_incluidos || '';
			datosTecnicos = JSON.stringify(p.datos_tecnicos || {}, null, 2);
			precio = String(p.precio);
			imagen = p.imagen || '';
			unidad_id = p.unidad_venta_id;
			categoria_ids = p.categorias.map((c) => c.id);
			etiqueta_ids_str = p.etiquetas.map((e) => e.id).join(', ');
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function slugify(s) {
		return s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
	}

	async function submit(e) {
		e.preventDefault();
		saving = true;
		error = null;
		success = null;
		let parsedDatos = {};
		try {
			parsedDatos = datosTecnicos ? JSON.parse(datosTecnicos) : {};
		} catch {
			error = 'datos_tecnicos JSON inválido';
			saving = false;
			return;
		}
		const etiqueta_ids = etiqueta_ids_str.split(',').map((s) => s.trim()).filter(Boolean);
		const payload = {
			titulo,
			slug: slugify(slug),
			descripcion: descripcion || null,
			componentes_incluidos: componentes || null,
			datos_tecnicos: parsedDatos,
			precio: precio,
			imagen: imagen || null,
			unidad_venta_id: unidad_id,
			categoria_ids,
			etiqueta_ids
		};
		try {
			await api.put(`/products/${id}`, payload);
			success = 'Producto actualizado';
			setTimeout(() => goto(`/productos/${id}`), 700);
		} catch (err) {
			const d = err.data?.detail;
			error = typeof d === 'string' ? d : d ? JSON.stringify(d) : err.message;
		} finally {
			saving = false;
		}
	}

	onMount(fetchAll);
</script>

<svelte:head>
	<title>Editar producto — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4 max-w-3xl">
	<a href="/productos/{id}" class="text-sm underline">← Volver al producto</a>
	<h1 class="font-oswald font-bold text-xl">Editar producto</h1>

	{#if loading}
		<Skeleton class="h-64 w-full" />
	{:else}
		{#if error}<Alert variant="destructive"><p class="text-sm whitespace-pre-wrap">{error}</p></Alert>{/if}
		{#if success}<Alert><p class="text-sm">{success}</p></Alert>{/if}

		<Card class="p-4">
			<form onsubmit={submit} class="flex flex-col gap-4">
				<div class="grid md:grid-cols-2 gap-3">
					<label class="flex flex-col gap-1 text-sm">
						<span class="font-oswald font-bold">Título *</span>
						<Input bind:value={titulo} required />
					</label>
					<label class="flex flex-col gap-1 text-sm">
						<span class="font-oswald font-bold">Slug *</span>
						<Input bind:value={slug} required />
					</label>
				</div>

				<label class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Descripción</span>
					<textarea bind:value={descripcion} rows="3" class="border bg-background px-3 py-2 text-sm"></textarea>
				</label>

				<label class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Componentes incluidos</span>
					<Input bind:value={componentes} />
				</label>

				<label class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Datos técnicos (JSON)</span>
					<textarea bind:value={datosTecnicos} rows="3" class="border bg-background px-3 py-2 text-sm font-mono text-xs"></textarea>
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
						<Input bind:value={imagen} />
					</label>
				</div>

				<div class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Categorías *</span>
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

				<label class="flex flex-col gap-1 text-sm">
					<span class="font-oswald font-bold">Etiquetas (UUIDs comma)</span>
					<Input bind:value={etiqueta_ids_str} placeholder="IDs separados por coma" />
					<span class="text-xs text-muted-foreground">Disponibles: {etiquetas.map((e) => e.slug).join(', ')}</span>
				</label>

				<Button type="submit" disabled={saving}>{saving ? 'Guardando…' : 'Guardar cambios'}</Button>
			</form>
		</Card>
	{/if}
</div>
