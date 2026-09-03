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
	let categoriaError = $state(null);

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
	let categoriasTree = $state([]);
	let categoriasFlat = $state([]);
	let etiquetas = $state([]);

	function buildTreeClient(cats) {
		const byId = {};
		for (const c of cats) byId[c.id] = { ...c, children: [] };
		const roots = [];
		for (const c of cats) {
			const node = byId[c.id];
			if (c.parent_id) {
				const parent = byId[c.parent_id];
				if (parent) parent.children.push(node);
				else roots.push(node);
			} else {
				roots.push(node);
			}
		}
		roots.sort((a, b) => a.nombre.localeCompare(b.nombre));
		for (const r of roots) r.children.sort((a, b) => a.nombre.localeCompare(b.nombre));
		return roots;
	}

	function validateCategoriaSelection() {
		if (!categoria_ids.length) return 'Debe seleccionar al menos una categoría (RN-01)';
		const byId = {};
		for (const c of categoriasFlat) byId[c.id] = c;
		const hasLeaf = categoria_ids.some((i) => byId[i]?.nivel === 2);
		if (hasLeaf) return null;
		for (const selId of categoria_ids) {
			const hasChildren = categoriasFlat.some((c) => c.parent_id === selId);
			if (hasChildren) return 'Debe asignar al menos una subcategoría hoja (nivel 2) — RN-38';
		}
		return null;
	}

	function toggleCategoria(catId, checked) {
		if (checked) categoria_ids = [...categoria_ids, catId];
		else categoria_ids = categoria_ids.filter((x) => x !== catId);
		categoriaError = validateCategoriaSelection();
	}

	async function fetchAll() {
		loading = true;
		try {
			unidades = await api.get('/unidades-medida');
			etiquetas = await api.get('/etiquetas');
			let cats;
			try {
				cats = await api.get('/categorias', { tree: true });
			} catch {
				cats = await api.get('/categorias');
			}
			if (Array.isArray(cats) && cats.length && cats[0].children !== undefined) {
				categoriasTree = cats;
				categoriasFlat = [];
				for (const r of cats) {
					categoriasFlat.push({ ...r, children: undefined });
					for (const ch of r.children || []) categoriasFlat.push(ch);
				}
			} else if (Array.isArray(cats)) {
				categoriasFlat = cats;
				categoriasTree = buildTreeClient(cats);
			}
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
		categoriaError = validateCategoriaSelection();
		if (categoriaError) {
			error = categoriaError;
			saving = false;
			return;
		}
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
					<span class="font-oswald font-bold">Categorías * — árbol 2 niveles (RN-38)</span>
					{#if categoriasTree.length}
						<div class="flex flex-col gap-2 border p-2 bg-muted/20">
							{#each categoriasTree as root (root.id)}
								<div class="border bg-background p-2">
									<label class="flex items-center gap-2 text-xs font-medium cursor-pointer">
										<input type="checkbox" checked={categoria_ids.includes(root.id)} onchange={(e) => toggleCategoria(root.id, e.target.checked)} />
										<span class="w-3 h-3 border inline-block" style="background:{root.color}"></span>
										{root.nombre}
										<span class="font-mono text-[10px] text-muted-foreground">({root.slug})</span>
										<span class="text-[10px] px-1 border bg-muted">nivel {root.nivel}</span>
									</label>
									{#if root.children?.length}
										<div class="pl-6 mt-2 flex flex-wrap gap-2 border-t pt-2">
											{#each root.children as child (child.id)}
												<label class="flex items-center gap-1 text-xs border px-2 py-1 bg-muted/30 cursor-pointer">
													<input type="checkbox" checked={categoria_ids.includes(child.id)} onchange={(e) => toggleCategoria(child.id, e.target.checked)} />
													<span class="w-3 h-3 border inline-block" style="background:{child.color}"></span>
													<span>{root.nombre} › {child.nombre}</span>
												</label>
											{/each}
										</div>
									{/if}
								</div>
							{/each}
						</div>
					{:else if categoriasFlat.length}
						<div class="flex flex-wrap gap-2 border p-2 bg-muted/20">
							{#each categoriasFlat as c}
								<label class="flex items-center gap-1 text-xs border px-2 py-1 bg-background cursor-pointer">
									<input type="checkbox" checked={categoria_ids.includes(c.id)} onchange={(e) => toggleCategoria(c.id, e.target.checked)} />
									<span class="w-3 h-3 border inline-block" style="background:{c.color}"></span>
									{#if c.parent_id}
										{categoriasFlat.find((p) => p.id === c.parent_id)?.nombre} › {c.nombre}
									{:else}
										{c.nombre}
									{/if}
								</label>
							{/each}
						</div>
					{:else}
						<div class="border p-3 text-xs text-muted-foreground">Sin categorías</div>
					{/if}
					{#if categoriaError}
						<span class="text-xs text-destructive">{categoriaError}</span>
					{:else}
						<span class="text-xs text-muted-foreground">Al menos una hoja nivel 2 requerida si su padre tiene hijas. Gestionar en <a href="/categorias" class="underline">Categorías</a>.</span>
					{/if}
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
