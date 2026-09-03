<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Badge from '$lib/components/ui/badge.svelte';

	let items = $state([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state(null);
	let limit = 50;
	let offset = $state(0);

	let editingId = $state(null);
	let editDisponible = $state('');
	let editReservada = $state('');
	let saving = $state(false);
	let productTitles = $state({}); // product_id -> titulo
	let productLoading = $state(false);

	async function fetchStock() {
		loading = true;
		error = null;
		try {
			const data = await api.get('/admin/stock', { limit, offset });
			items = data.items || [];
			total = data.total ?? items.length;
			// enrich with product titles (best effort)
			fetchTitles(items);
		} catch (e) {
			if (e.status === 401) error = 'No autenticado (401)';
			else if (e.status === 403) error = 'Acceso denegado (403)';
			else error = e.message;
			items = [];
		} finally {
			loading = false;
		}
	}

	async function fetchTitles(rows) {
		productLoading = true;
		// try fetch each product title via /products/{id} or bulk; best-effort ignore errors
		const ids = rows.map((r) => r.product_id).filter((id) => !productTitles[id]);
		if (ids.length === 0) {
			productLoading = false;
			return;
		}
		for (const pid of ids) {
			try {
				// try admin product fetch; fallback to public
				let p = null;
				try {
					p = await api.get(`/products/${pid}`);
				} catch {
					// try list filter
					p = null;
				}
				if (p?.titulo) productTitles[pid] = p.titulo;
				else productTitles[pid] = pid.slice(0, 8) + '…';
			} catch {
				productTitles[pid] = pid.slice(0, 8) + '…';
			}
		}
		productLoading = false;
	}

	function startEdit(row) {
		editingId = row.product_id;
		editDisponible = String(row.cantidad_disponible);
		editReservada = String(row.cantidad_reservada);
	}
	function cancelEdit() {
		editingId = null;
	}

	async function saveEdit(row) {
		saving = true;
		try {
			const body = {};
			if (editDisponible !== '') body.cantidad_disponible = editDisponible;
			if (editReservada !== '') body.cantidad_reservada = editReservada;
			const updated = await api.put(`/admin/stock/${row.product_id}`, body);
			// update local row
			const idx = items.findIndex((r) => r.product_id === row.product_id);
			if (idx !== -1) items[idx] = updated;
			editingId = null;
		} catch (e) {
			if (e.status === 403) alert('Solo Administrador puede ajustar stock (PUT requiere admin)');
			else alert('Error ajustar stock: ' + e.message);
		} finally {
			saving = false;
		}
	}

	function nextPage() {
		if (offset + limit < total) {
			offset += limit;
			fetchStock();
		}
	}
	function prevPage() {
		if (offset > 0) {
			offset = Math.max(0, offset - limit);
			fetchStock();
		}
	}

	onMount(fetchStock);
</script>

<svelte:head>
	<title>Stock — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
		<div>
			<h1 class="font-oswald font-bold text-xl">Stock por producto</h1>
			<p class="text-xs text-muted-foreground">RN-35: disponible / reservada · movimientos reserva/confirmacion/devolucion/ajuste · GET /admin/stock y PUT /admin/stock/&#123;product_id&#125; (solo admin).</p>
		</div>
		<Button variant="outline" size="sm" onclick={fetchStock}>Recargar</Button>
	</div>

	<Card class="p-3 flex flex-col gap-2">
		<div class="flex items-center gap-2 text-xs">
			<span class="font-oswald font-bold">Total registros: {total}</span>
			<span class="text-muted-foreground">· Página {Math.floor(offset / limit) + 1} de {Math.ceil(total / limit) || 1}</span>
			<span class="ml-auto text-muted-foreground hidden md:inline">Ajuste manual registra movimiento tipo "ajuste"</span>
		</div>
	</Card>

	{#if error}
		<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
	{/if}

	{#if loading}
		<Skeleton class="h-64 w-full" />
	{:else}
		<Card class="overflow-hidden">
			<div class="overflow-auto">
				<table class="w-full text-sm">
					<thead class="bg-muted">
						<tr class="text-left font-oswald text-xs tracking-wide">
							<th class="px-3 py-2">Producto</th>
							<th class="px-3 py-2">Disponible</th>
							<th class="px-3 py-2">Reservada</th>
							<th class="px-3 py-2">Actualizado</th>
							<th class="px-3 py-2">Acciones</th>
						</tr>
					</thead>
					<tbody>
						{#each items as row (row.product_id)}
							<tr class="border-t hover:bg-muted/50">
								<td class="px-3 py-2">
									<div class="font-medium text-xs">{productTitles[row.product_id] || row.product_id.slice(0, 8) + '…'}</div>
									<div class="font-mono text-xs text-muted-foreground">{row.product_id}</div>
									{#if productLoading}<span class="text-xs text-muted-foreground">cargando título…</span>{/if}
								</td>
								<td class="px-3 py-2">
									{#if editingId === row.product_id}
										<Input bind:value={editDisponible} type="number" step="0.01" class="w-24 h-8 text-sm" />
									{:else}
										<Badge variant="secondary">{Number(row.cantidad_disponible).toFixed(2)}</Badge>
									{/if}
								</td>
								<td class="px-3 py-2">
									{#if editingId === row.product_id}
										<Input bind:value={editReservada} type="number" step="0.01" class="w-24 h-8 text-sm" />
									{:else}
										<span class="inline-flex px-2 py-0.5 border text-xs bg-[#7c3aed]/10 border-[#7c3aed]/30 text-[#7c3aed] font-oswald font-bold">{Number(row.cantidad_reservada).toFixed(2)}</span>
									{/if}
								</td>
								<td class="px-3 py-2 text-xs text-muted-foreground">{row.updated_at ? new Date(row.updated_at).toLocaleString('es-AR') : '—'}</td>
								<td class="px-3 py-2 flex gap-1">
									{#if editingId === row.product_id}
										<Button size="sm" onclick={() => saveEdit(row)} disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</Button>
										<Button variant="outline" size="sm" onclick={cancelEdit}>Cancelar</Button>
									{:else}
										<button onclick={() => startEdit(row)} class="border px-2 py-1 text-xs hover:bg-accent">Ajustar</button>
										<a href="/productos/{row.product_id}" class="border px-2 py-1 text-xs hover:bg-accent">Ver producto</a>
									{/if}
								</td>
							</tr>
						{/each}
						{#if items.length === 0}
							<tr><td colspan="5" class="px-3 py-6 text-center text-muted-foreground">Sin registros de stock — los productos sin movimiento aún no tienen fila (se crea al reservar o ajustar).</td></tr>
						{/if}
					</tbody>
				</table>
			</div>
			<div class="flex items-center justify-between p-3 border-t bg-muted/20">
				<span class="text-xs">Total: {total}</span>
				<div class="flex gap-2">
					<Button variant="outline" size="sm" onclick={prevPage} disabled={offset === 0}>Anterior</Button>
					<Button variant="outline" size="sm" onclick={nextPage} disabled={offset + limit >= total}>Siguiente</Button>
				</div>
			</div>
		</Card>
		<p class="text-xs text-muted-foreground">Tip: el stock vive separado de <code class="bg-muted px-1">productos</code> (RN-35). Si un producto no aparece aquí, use "Ajustar" via PUT se crea la fila en 0 o consulte su stock con GET /admin/stock/&#123;id&#125;.</p>
	{/if}
</div>
