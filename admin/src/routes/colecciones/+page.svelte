<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Dialog from '$lib/components/ui/dialog.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';

	let colecciones = $state([]);
	let loading = $state(true);
	let error = $state(null);
	let success = $state(null);
	let filterDestacada = $state(''); // '', 'true', 'false'

	let showCreate = $state(false);
	let showEdit = $state(false);
	let editing = $state(null);
	let saving = $state(false);
	let formError = $state(null);

	let formNombre = $state('');
	let formSlug = $state('');
	let formDescripcion = $state('');
	let formImagen = $state('');
	let formDestacada = $state(false);

	function slugify(s) {
		return s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
	}

	async function fetchColecciones() {
		loading = true;
		error = null;
		try {
			const params = {};
			if (filterDestacada === 'true') params.destacada = true;
			else if (filterDestacada === 'false') params.destacada = false;
			colecciones = await api.get('/colecciones', params);
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function openCreate() {
		formNombre = '';
		formSlug = '';
		formDescripcion = '';
		formImagen = '';
		formDestacada = false;
		formError = null;
		showCreate = true;
	}

	function openEdit(c) {
		editing = c;
		formNombre = c.nombre;
		formSlug = c.slug;
		formDescripcion = c.descripcion || '';
		formImagen = c.imagen || '';
		formDestacada = !!c.destacada;
		formError = null;
		showEdit = true;
	}

	async function handleCreate() {
		if (!formNombre.trim()) { formError = 'Nombre requerido'; return; }
		const slug = slugify(formSlug || formNombre);
		if (!slug) { formError = 'Slug requerido'; return; }
		saving = true;
		formError = null;
		try {
			const payload = {
				nombre: formNombre.trim(),
				slug,
				descripcion: formDescripcion || null,
				imagen: formImagen || null,
				destacada: !!formDestacada
			};
			await api.post('/colecciones', payload);
			success = `Colección "${payload.nombre}" creada`;
			showCreate = false;
			await fetchColecciones();
			setTimeout(() => (success = null), 2500);
		} catch (e) {
			const d = e.data?.detail;
			formError = typeof d === 'string' ? d : d ? JSON.stringify(d) : e.message;
		} finally {
			saving = false;
		}
	}

	async function handleEdit() {
		if (!editing) return;
		if (!formNombre.trim()) { formError = 'Nombre requerido'; return; }
		const slug = slugify(formSlug || formNombre);
		saving = true;
		formError = null;
		try {
			const payload = {
				nombre: formNombre.trim(),
				slug,
				descripcion: formDescripcion || null,
				imagen: formImagen || null,
				destacada: !!formDestacada
			};
			await api.put(`/colecciones/${editing.id}`, payload);
			success = `Colección "${payload.nombre}" actualizada`;
			showEdit = false;
			editing = null;
			await fetchColecciones();
			setTimeout(() => (success = null), 2500);
		} catch (e) {
			const d = e.data?.detail;
			formError = typeof d === 'string' ? d : d ? JSON.stringify(d) : e.message;
		} finally {
			saving = false;
		}
	}

	async function handleDelete(c) {
		if (!confirm(`¿Eliminar colección "${c.nombre}"? Se limpiarán sus vínculos N:M sin afectar productos.`)) return;
		try {
			await api.delete(`/colecciones/${c.id}`);
			success = `Colección "${c.nombre}" eliminada`;
			await fetchColecciones();
			setTimeout(() => (success = null), 2500);
		} catch (e) {
			error = e.message;
		}
	}

	async function toggleDestacada(c) {
		try {
			await api.put(`/colecciones/${c.id}`, { destacada: !c.destacada });
			await fetchColecciones();
		} catch (e) {
			error = e.message;
		}
	}

	onMount(fetchColecciones);
</script>

<svelte:head>
	<title>Colecciones — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
		<div>
			<h1 class="font-oswald font-bold text-xl">Colecciones — grupos curados</h1>
			<p class="text-xs text-muted-foreground">RN-39 · N:M con productos · destacada para home · GET /colecciones?destacada · slug único (RN-20)</p>
		</div>
		<div class="flex gap-2">
			<Button variant="outline" size="sm" onclick={fetchColecciones}>Actualizar</Button>
			<Button size="sm" onclick={openCreate}>+ Nueva colección</Button>
		</div>
	</div>

	<Card class="p-3 flex flex-col md:flex-row gap-2 items-center">
		<label class="flex items-center gap-2 text-sm">
			<span class="font-oswald font-bold">Filtro destacada</span>
			<select bind:value={filterDestacada} onchange={fetchColecciones} class="border bg-background px-3 py-2 text-sm h-9">
				<option value="">Todas</option>
				<option value="true">Destacadas</option>
				<option value="false">No destacadas</option>
			</select>
		</label>
		<span class="text-xs text-muted-foreground">Total: {colecciones.length} · destacadas: {colecciones.filter(c=>c.destacada).length}</span>
	</Card>

	{#if error}<Alert variant="destructive"><p class="text-sm whitespace-pre-wrap">{error}</p></Alert>{/if}
	{#if success}<Alert><p class="text-sm">{success}</p></Alert>{/if}

	{#if loading}
		<Skeleton class="h-64 w-full" />
	{:else if colecciones.length === 0}
		<Card class="p-6 text-center text-sm text-muted-foreground">Sin colecciones. Creá la primera con “+ Nueva colección”.</Card>
	{:else}
		<Card class="overflow-hidden">
			<div class="overflow-auto">
				<table class="w-full text-sm">
					<thead class="bg-muted">
						<tr class="text-left font-oswald text-xs tracking-wide">
							<th class="px-3 py-2">Nombre</th>
							<th class="px-3 py-2">Slug</th>
							<th class="px-3 py-2">Destacada</th>
							<th class="px-3 py-2">Productos</th>
							<th class="px-3 py-2">Actualizado</th>
							<th class="px-3 py-2">Acciones</th>
						</tr>
					</thead>
					<tbody>
						{#each colecciones as c (c.id)}
							<tr class="border-t hover:bg-muted/50">
								<td class="px-3 py-2 font-medium">{c.nombre}</td>
								<td class="px-3 py-2 font-mono text-xs">{c.slug}</td>
								<td class="px-3 py-2">
									{#if c.destacada}
										<Badge variant="secondary">★ destacada</Badge>
									{:else}
										<Badge variant="outline">no</Badge>
									{/if}
								</td>
								<td class="px-3 py-2 text-xs">{c.productos_count ?? 0}</td>
								<td class="px-3 py-2 text-xs text-muted-foreground">{new Date(c.updated_at).toLocaleString()}</td>
								<td class="px-3 py-2 flex flex-wrap gap-1">
									<a href="/colecciones/{c.id}" class="border px-2 py-1 text-xs hover:bg-accent">Ver</a>
									<button onclick={() => openEdit(c)} class="border px-2 py-1 text-xs hover:bg-accent">Editar</button>
									<button onclick={() => toggleDestacada(c)} class="border px-2 py-1 text-xs hover:bg-accent">{c.destacada ? 'Quitar destacada' : 'Destacar'}</button>
									<button onclick={() => handleDelete(c)} class="border px-2 py-1 text-xs hover:bg-accent text-destructive">Eliminar</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</Card>
	{/if}
</div>

<Dialog bind:open={showCreate} title="Nueva colección">
	{#if formError}<Alert variant="destructive" class="mb-3"><p class="text-sm whitespace-pre-wrap">{formError}</p></Alert>{/if}
	<form onsubmit={(e)=>{e.preventDefault(); handleCreate();}} class="flex flex-col gap-3">
		<label class="flex flex-col gap-1 text-sm">
			<span class="font-oswald font-bold">Nombre *</span>
			<Input bind:value={formNombre} required placeholder="Ej: Verano 2026" oninput={()=>{ if(!formSlug) formSlug = slugify(formNombre); }} />
		</label>
		<label class="flex flex-col gap-1 text-sm">
			<span class="font-oswald font-bold">Slug *</span>
			<Input bind:value={formSlug} required placeholder="auto desde nombre" />
			<span class="text-xs text-muted-foreground">único, lowercase con guiones</span>
		</label>
		<label class="flex flex-col gap-1 text-sm">
			<span class="font-oswald font-bold">Descripción</span>
			<textarea bind:value={formDescripcion} rows="2" class="border bg-background px-3 py-2 text-sm" placeholder="Opcional"></textarea>
		</label>
		<label class="flex flex-col gap-1 text-sm">
			<span class="font-oswald font-bold">Imagen URL</span>
			<Input bind:value={formImagen} placeholder="https://..." />
		</label>
		<label class="flex items-center gap-2 text-sm">
			<input type="checkbox" bind:checked={formDestacada} />
			<span class="font-oswald font-bold">Destacada (home)</span>
		</label>
		<div class="flex gap-2 justify-end pt-2">
			<Button type="button" variant="outline" onclick={()=> (showCreate=false)}>Cancelar</Button>
			<Button type="submit" disabled={saving}>{saving?'Guardando…':'Crear'}</Button>
		</div>
	</form>
</Dialog>

<Dialog bind:open={showEdit} title="Editar colección">
	{#if editing}
		{#if formError}<Alert variant="destructive" class="mb-3"><p class="text-sm whitespace-pre-wrap">{formError}</p></Alert>{/if}
		<form onsubmit={(e)=>{e.preventDefault(); handleEdit();}} class="flex flex-col gap-3">
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Nombre *</span>
				<Input bind:value={formNombre} required />
			</label>
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Slug *</span>
				<Input bind:value={formSlug} required />
			</label>
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Descripción</span>
				<textarea bind:value={formDescripcion} rows="2" class="border bg-background px-3 py-2 text-sm"></textarea>
			</label>
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Imagen URL</span>
				<Input bind:value={formImagen} />
			</label>
			<label class="flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={formDestacada} />
				<span class="font-oswald font-bold">Destacada</span>
			</label>
			<div class="flex gap-2 justify-end pt-2">
				<Button type="button" variant="outline" onclick={()=> (showEdit=false)}>Cancelar</Button>
				<Button type="submit" disabled={saving}>{saving?'Guardando…':'Guardar cambios'}</Button>
			</div>
		</form>
	{/if}
</Dialog>
