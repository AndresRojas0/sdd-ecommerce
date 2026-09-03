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

	let tree = $state([]);
	let flat = $state([]);
	let loading = $state(true);
	let error = $state(null);
	let success = $state(null);
	let expandedIds = $state(new Set());
	let filterQuery = $state('');

	// dialog state
	let showCreate = $state(false);
	let showEdit = $state(false);
	let formNombre = $state('');
	let formSlug = $state('');
	let formColor = $state('#e85d04');
	let formParentId = $state('');
	let editingCat = $state(null);
	let saving = $state(false);
	let formError = $state(null);

	function slugify(s) {
		return s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
	}

	$effect(() => {
		if (formNombre && !formSlug) {
			// only auto-slugify if user hasn't manually edited slug for new
		}
	});

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

	async function fetchCategorias() {
		loading = true;
		error = null;
		try {
			let data;
			try {
				data = await api.get('/categorias', { tree: true });
			} catch {
				data = await api.get('/categorias');
			}
			// detect tree vs flat
			if (Array.isArray(data) && data.length && data[0].children !== undefined) {
				tree = data;
				// flatten for select
				flat = [];
				for (const r of tree) {
					flat.push(r);
					for (const ch of r.children || []) flat.push(ch);
				}
				// expand all by default
				expandedIds = new Set(tree.map((r) => r.id));
			} else if (Array.isArray(data)) {
				flat = data;
				tree = buildTreeClient(data);
				expandedIds = new Set(tree.map((r) => r.id));
			} else {
				tree = [];
				flat = [];
			}
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function toggleExpand(id) {
		const next = new Set(expandedIds);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		expandedIds = next;
	}

	function openCreate(parentId = '') {
		formNombre = '';
		formSlug = '';
		formColor = '#e85d04';
		formParentId = parentId ? String(parentId) : '';
		formError = null;
		showCreate = true;
	}

	function openCreateTop() {
		openCreate('');
	}

	function openCreateSub(parentId) {
		openCreate(parentId);
	}

	function openEdit(cat) {
		editingCat = cat;
		formNombre = cat.nombre;
		formSlug = cat.slug;
		formColor = cat.color || '#e85d04';
		formParentId = cat.parent_id ? String(cat.parent_id) : '';
		formError = null;
		showEdit = true;
	}

	async function handleCreate() {
		if (!formNombre.trim()) {
			formError = 'Nombre requerido';
			return;
		}
		const slug = slugify(formSlug || formNombre);
		if (!slug) {
			formError = 'Slug requerido';
			return;
		}
		if (!/^#[0-9A-Fa-f]{6}$/.test(formColor)) {
			formError = 'Color debe ser hex #RRGGBB';
			return;
		}
		saving = true;
		formError = null;
		try {
			const payload = {
				nombre: formNombre.trim(),
				slug,
				color: formColor,
				parent_id: formParentId ? formParentId : null
			};
			await api.post('/categorias', payload);
			success = `Categoría "${payload.nombre}" creada`;
			showCreate = false;
			await fetchCategorias();
			setTimeout(() => (success = null), 3000);
		} catch (e) {
			const d = e.data?.detail;
			formError = typeof d === 'string' ? d : d ? JSON.stringify(d) : e.message;
		} finally {
			saving = false;
		}
	}

	async function handleEdit() {
		if (!editingCat) return;
		if (!formNombre.trim()) {
			formError = 'Nombre requerido';
			return;
		}
		const slug = slugify(formSlug || formNombre);
		saving = true;
		formError = null;
		try {
			const payload = {
				nombre: formNombre.trim(),
				slug,
				color: formColor,
				parent_id: formParentId ? formParentId : null
			};
			// For move logic: if editingCat was nivel1 with children, backend will reject moving to nivel2.
			// We send parent_id explicitly; if unchanged and nivel1, backend handles.
			await api.put(`/categorias/${editingCat.id}`, payload);
			success = `Categoría "${payload.nombre}" actualizada`;
			showEdit = false;
			editingCat = null;
			await fetchCategorias();
			setTimeout(() => (success = null), 3000);
		} catch (e) {
			const d = e.data?.detail;
			formError = typeof d === 'string' ? d : d ? JSON.stringify(d) : e.message;
		} finally {
			saving = false;
		}
	}

	async function handleDelete(cat) {
		const hasChildren = cat.children && cat.children.length > 0;
		const msg = hasChildren
			? `¿Eliminar "${cat.nombre}"? Tiene ${cat.children.length} subcategoría(s). Fallará con 409 si tiene hijas.`
			: `¿Eliminar categoría "${cat.nombre}"? Fallará con 409 si está en uso por productos.`;
		if (!confirm(msg)) return;
		error = null;
		success = null;
		try {
			await api.delete(`/categorias/${cat.id}`);
			success = `Categoría "${cat.nombre}" eliminada`;
			await fetchCategorias();
			setTimeout(() => (success = null), 3000);
		} catch (e) {
			const d = e.data?.detail;
			error = typeof d === 'string' ? d : d ? JSON.stringify(d) : e.message;
		}
	}

	function rootsFiltered() {
		if (!filterQuery.trim()) return tree;
		const q = filterQuery.toLowerCase();
		return tree
			.map((r) => {
				const rootMatch = r.nombre.toLowerCase().includes(q) || r.slug.toLowerCase().includes(q);
				const matchingChildren = (r.children || []).filter(
					(c) => c.nombre.toLowerCase().includes(q) || c.slug.toLowerCase().includes(q)
				);
				if (rootMatch) return r;
				if (matchingChildren.length) return { ...r, children: matchingChildren };
				return null;
			})
			.filter(Boolean);
	}

	let rootsNivel1 = $derived(flat.filter((c) => c.nivel === 1));

	onMount(fetchCategorias);
</script>

<svelte:head>
	<title>Categorías — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
		<div>
			<h1 class="font-oswald font-bold text-xl">Categorías — árbol 2 niveles</h1>
			<p class="text-xs text-muted-foreground">RN-01 / RN-38 · Crear nivel 1 (parent_id null) y subcategoría nivel 2 · DELETE 409 si tiene hijas o productos</p>
		</div>
		<div class="flex gap-2">
			<Button variant="outline" size="sm" onclick={fetchCategorias}>Actualizar</Button>
			<Button size="sm" onclick={openCreateTop}>+ Nueva categoría</Button>
		</div>
	</div>

	<Card class="p-3 flex flex-col md:flex-row gap-2">
		<Input bind:value={filterQuery} placeholder="Filtrar por nombre o slug…" class="md:max-w-sm" />
		<span class="text-xs text-muted-foreground self-center">Total raíces: {tree.length} · Total categorías: {flat.length} · GET /categorias?tree=true</span>
	</Card>

	{#if error}<Alert variant="destructive"><p class="text-sm whitespace-pre-wrap">{error}</p></Alert>{/if}
	{#if success}<Alert><p class="text-sm">{success}</p></Alert>{/if}

	{#if loading}
		<Skeleton class="h-64 w-full" />
	{:else if rootsFiltered().length === 0}
		<Card class="p-6 text-center text-sm text-muted-foreground">
			{#if flat.length === 0}
				Sin categorías. Creá la primera categoría nivel 1.
			{:else}
				Sin resultados para "{filterQuery}"
			{/if}
		</Card>
	{:else}
		<div class="flex flex-col gap-3">
			{#each rootsFiltered() as root (root.id)}
				<Card class="overflow-hidden">
					<div class="flex items-center gap-3 p-3 bg-muted/20 border-b">
						<button
							onclick={() => toggleExpand(root.id)}
							class="w-6 h-6 border bg-background flex items-center justify-center text-xs hover:bg-accent"
							aria-label="Expandir"
						>
							{expandedIds.has(root.id) ? '−' : '+'}
						</button>
						<span class="w-4 h-4 border inline-block shrink-0" style="background:{root.color}" title={root.color}></span>
						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-2 flex-wrap">
								<span class="font-oswald font-bold text-sm truncate">{root.nombre}</span>
								<Badge variant="secondary">nivel {root.nivel}</Badge>
								<span class="font-mono text-xs text-muted-foreground">{root.slug}</span>
								{#if root.children?.length}
									<Badge variant="outline">{root.children.length} hijas</Badge>
								{/if}
							</div>
						</div>
						<div class="flex flex-wrap gap-1">
							<Button size="sm" variant="outline" onclick={() => openCreateSub(root.id)}>+ Subcategoría</Button>
							<Button size="sm" variant="outline" onclick={() => openEdit(root)}>Editar</Button>
							<Button size="sm" variant="destructive" onclick={() => handleDelete(root)}>Eliminar</Button>
						</div>
					</div>

					{#if expandedIds.has(root.id)}
						{#if root.children && root.children.length}
							<div class="divide-y">
								{#each root.children as child (child.id)}
									<div class="flex items-center gap-3 p-3 pl-8 bg-background hover:bg-muted/20">
										<span class="text-muted-foreground text-xs">↳</span>
										<span class="w-4 h-4 border inline-block shrink-0" style="background:{child.color}" title={child.color}></span>
										<div class="flex-1 min-w-0">
											<div class="flex items-center gap-2 flex-wrap">
												<span class="font-medium text-sm">{child.nombre}</span>
												<Badge variant="outline">nivel {child.nivel}</Badge>
												<span class="font-mono text-xs text-muted-foreground">{child.slug} · parent {root.slug}</span>
											</div>
										</div>
										<div class="flex gap-1">
											<Button size="sm" variant="outline" onclick={() => openEdit(child)}>Editar</Button>
											<Button size="sm" variant="destructive" onclick={() => handleDelete(child)}>Eliminar</Button>
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<div class="p-3 pl-8 text-xs text-muted-foreground">Sin subcategorías. Usá “+ Subcategoría” para crear hijas (nivel 2).</div>
						{/if}
					{/if}
				</Card>
			{/each}
		</div>
	{/if}
</div>

<!-- Create Dialog -->
<Dialog bind:open={showCreate} title={formParentId ? 'Nueva subcategoría' : 'Nueva categoría'}>
	{#if formError}<Alert variant="destructive" class="mb-3"><p class="text-sm whitespace-pre-wrap">{formError}</p></Alert>{/if}
	<form onsubmit={(e) => { e.preventDefault(); handleCreate(); }} class="flex flex-col gap-3">
		<label class="flex flex-col gap-1 text-sm">
			<span class="font-oswald font-bold">Nombre *</span>
			<Input bind:value={formNombre} required placeholder="Ej: Bazar, Tornillos..." oninput={() => { if (!formSlug || formSlug === slugify(formNombre.slice(0,-1))) formSlug = slugify(formNombre); }} />
		</label>
		<label class="flex flex-col gap-1 text-sm">
			<span class="font-oswald font-bold">Slug *</span>
			<Input bind:value={formSlug} required placeholder="auto desde nombre" />
			<span class="text-xs text-muted-foreground">se genera lowercase con guiones; único (RN-20)</span>
		</label>
		<label class="flex flex-col gap-1 text-sm">
			<span class="font-oswald font-bold">Color *</span>
			<div class="flex gap-2 items-center">
				<input type="color" bind:value={formColor} class="h-10 w-14 border p-1 bg-background" />
				<Input bind:value={formColor} placeholder="#RRGGBB" class="flex-1" />
			</div>
		</label>
		<label class="flex flex-col gap-1 text-sm">
			<span class="font-oswald font-bold">Padre (parent_id)</span>
			<select bind:value={formParentId} class="border bg-background px-3 py-2 text-sm h-10">
				<option value="">— Sin padre — nivel 1 (categoría raíz)</option>
				{#each rootsNivel1 as r}
					<option value={r.id}>{r.nombre} ({r.slug}) — nivel 1</option>
				{/each}
			</select>
			<span class="text-xs text-muted-foreground">Si seleccionás padre, se crea como nivel 2. Debe ser nivel 1 (profundidad máx. 2, RN-38).</span>
		</label>
		<div class="flex gap-2 justify-end pt-2">
			<Button type="button" variant="outline" onclick={() => (showCreate = false)}>Cancelar</Button>
			<Button type="submit" disabled={saving}>{saving ? 'Guardando…' : 'Crear'}</Button>
		</div>
	</form>
</Dialog>

<!-- Edit Dialog -->
<Dialog bind:open={showEdit} title="Editar categoría">
	{#if editingCat}
		{#if formError}<Alert variant="destructive" class="mb-3"><p class="text-sm whitespace-pre-wrap">{formError}</p></Alert>{/if}
		<form onsubmit={(e) => { e.preventDefault(); handleEdit(); }} class="flex flex-col gap-3">
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Nombre *</span>
				<Input bind:value={formNombre} required />
			</label>
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Slug *</span>
				<Input bind:value={formSlug} required />
			</label>
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Color *</span>
				<div class="flex gap-2 items-center">
					<input type="color" bind:value={formColor} class="h-10 w-14 border p-1 bg-background" />
					<Input bind:value={formColor} />
				</div>
			</label>
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Padre (parent_id) — mover</span>
				<select bind:value={formParentId} class="border bg-background px-3 py-2 text-sm h-10">
					<option value="">— Sin padre — nivel 1</option>
					{#each rootsNivel1.filter(r => r.id !== editingCat.id) as r}
						<option value={r.id}>{r.nombre} ({r.slug})</option>
					{/each}
				</select>
				<span class="text-xs text-muted-foreground">Mover subcategoría entre padres: solo destino nivel 1. Si la categoría actual tiene hijas, no puede pasar a nivel 2 (409/422).</span>
			</label>
			<div class="flex gap-2 justify-end pt-2">
				<Button type="button" variant="outline" onclick={() => (showEdit = false)}>Cancelar</Button>
				<Button type="submit" disabled={saving}>{saving ? 'Guardando…' : 'Guardar cambios'}</Button>
			</div>
		</form>
	{/if}
</Dialog>
