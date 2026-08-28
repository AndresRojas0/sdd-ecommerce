<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Dialog from '$lib/components/ui/dialog.svelte';

	let pedido = $state(null);
	let loading = $state(true);
	let error = $state(null);
	let showReject = $state(false);
	let motivo = $state('');
	let showReassign = $state(false);
	let toVendedor = $state('');
	let vendedores = $state([]);
	let editingItems = $state(false);
	let editedItems = $state([]);
	let savingEdit = $state(false);
	let id = $derived($page.params.id);

	async function fetchPedido() {
		loading = true;
		error = null;
		try {
			pedido = await api.get(`/orders/${id}`);
			// also try admin orders endpoint? but /orders/{id} works for staff too
			editedItems = pedido.items.map((it) => ({ ...it, cantidad: String(it.cantidad) }));
		} catch (e) {
			// fallback try admin
			try {
				const data = await api.get('/admin/orders', { limit: 100, offset: 0 });
				pedido = data.items.find((p) => p.id === id) || null;
				if (!pedido) throw e;
			} catch (err) {
				error = e.message;
			}
		} finally {
			loading = false;
		}
	}

	async function fetchVendedores() {
		try {
			const data = await api.get('/admin/users', { role: 'vendedor', limit: 50, offset: 0 });
			vendedores = data.items.filter((u) => u.is_active);
		} catch {}
	}

	async function accept() {
		try {
			const res = await api.post(`/admin/orders/${id}/accept`, {});
			alert('Aceptado · OC ' + res.orden_compra.numero);
			await fetchPedido();
		} catch (e) {
			alert('Error aceptar: ' + e.message);
		}
	}

	async function reject() {
		if (!motivo.trim()) {
			alert('Motivo requerido');
			return;
		}
		try {
			await api.post(`/admin/orders/${id}/reject`, { motivo_rechazo: motivo });
			showReject = false;
			await fetchPedido();
		} catch (e) {
			alert('Error rechazar: ' + e.message);
		}
	}

	async function reassign() {
		if (!toVendedor) {
			alert('Seleccione vendedor');
			return;
		}
		try {
			await api.patch(`/admin/orders/${id}/reassign`, { to_vendedor_id: toVendedor });
			showReassign = false;
			await fetchPedido();
		} catch (e) {
			alert('Error reasignar: ' + e.message);
		}
	}

	async function saveEditedItems() {
		savingEdit = true;
		try {
			const items = editedItems.map((it) => ({
				product_id: it.product_id,
				cantidad: it.cantidad
			}));
			// PUT /orders/{id} expects {items: [{product_id, cantidad}]}
			// This endpoint is buyer-edit but staff can use it for pendiente? It checks owner.
			// For admin, we use same endpoint but as buyer owner? It will 403 if not owner.
			// Alternative: we can attempt PUT as admin? It checks pedido.user_id != current_user.id -> 403.
			// So admin cannot use PUT /orders. Instead we show note.
			// We will try PUT /orders/{id} and if 403, show workaround message.
			await api.put(`/orders/${id}`, { items });
			editingItems = false;
			await fetchPedido();
		} catch (e) {
			if (e.status === 403) {
				alert('Edición de items (UC-AD17/18) vía PUT /orders requiere ser el comprador creador. Para staff, edite antes de aceptar creando un pedido nuevo o use el flujo de corrección manual: el backend actual no expone PATCH admin para items. Como workaround, el vendedor puede recrear el pedido.');
			} else {
				alert('Error editar: ' + e.message);
			}
		} finally {
			savingEdit = false;
		}
	}

	onMount(() => {
		fetchPedido();
		fetchVendedores();
	});
</script>

<svelte:head>
	<title>Pedido {id.slice(0, 8)} — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<a href="/pedidos" class="text-sm underline">← Volver a pedidos</a>

	{#if loading}
		<Skeleton class="h-64 w-full" />
	{:else if error}
		<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
	{:else if pedido}
		<Card class="p-4 flex flex-col gap-3">
			<div class="flex flex-col md:flex-row justify-between gap-3">
				<div>
					<h1 class="font-oswald font-bold text-lg">Pedido {pedido.id}</h1>
					<p class="font-mono text-xs text-muted-foreground">Cliente: {pedido.user_id} · Vendedor: {pedido.vendedor_id || '—'} {pedido.orden_compra_id ? '· OC ' + pedido.orden_compra_id.slice(0, 8) : ''}</p>
					<p class="text-xs">Creado: {new Date(pedido.created_at).toLocaleString()} · Actualizado: {new Date(pedido.updated_at).toLocaleString()}</p>
				</div>
				<div class="flex flex-wrap gap-2 items-start">
					<Badge variant={pedido.estado === 'pendiente' ? 'outline' : pedido.estado === 'aceptado' ? 'secondary' : 'destructive'}>{pedido.estado}</Badge>
					<span class="font-oswald font-bold">Total: ${Number(pedido.total).toFixed(2)}</span>
				</div>
			</div>

			{#if pedido.motivo_rechazo}
				<Alert variant="destructive"><p class="text-sm">Motivo rechazo: {pedido.motivo_rechazo}</p></Alert>
			{/if}

			{#if pedido.orden_compra_id}
				<Alert><p class="text-sm">Orden de compra vinculada: <a href="/ordenes/{pedido.orden_compra_id}" class="underline font-mono">{pedido.orden_compra_id}</a></p></Alert>
			{/if}

			{#if pedido.estado === 'pendiente'}
				<div class="flex flex-wrap gap-2 border-t pt-3">
					<Button size="sm" variant="secondary" onclick={accept}>Aceptar → generar OC (UC-AD15)</Button>
					<Button size="sm" variant="destructive" onclick={() => (showReject = true)}>Rechazar (UC-AD16)</Button>
					<Button size="sm" variant="outline" onclick={() => (showReassign = true)}>Reasignar (RN-27)</Button>
					<Button size="sm" variant="outline" onclick={() => (editingItems = !editingItems)}>{editingItems ? 'Cancelar edición' : 'Corregir items (UC-AD17/18)'}</Button>
				</div>
			{/if}
		</Card>

		<Card class="p-4">
			<div class="flex items-center justify-between mb-2">
				<h3 class="font-oswald font-bold text-sm">Items ({pedido.items.length})</h3>
				<span class="text-xs text-muted-foreground">Subtotal: ${Number(pedido.subtotal).toFixed(2)}</span>
			</div>
			{#if !editingItems}
				<div class="overflow-auto">
					<table class="w-full text-sm">
						<thead class="bg-muted">
							<tr class="text-left font-oswald text-xs">
								<th class="px-3 py-2">Producto</th>
								<th class="px-3 py-2">Cantidad</th>
								<th class="px-3 py-2">Precio unitario</th>
								<th class="px-3 py-2">Subtotal</th>
							</tr>
						</thead>
						<tbody>
							{#each pedido.items as it}
								<tr class="border-t">
									<td class="px-3 py-2"><div class="font-medium">{it.producto_titulo || it.product_id.slice(0, 8)}</div><div class="font-mono text-xs text-muted-foreground">{it.product_id}</div></td>
									<td class="px-3 py-2">{it.cantidad}</td>
									<td class="px-3 py-2">${Number(it.precio_unitario).toFixed(2)}</td>
									<td class="px-3 py-2">${Number(it.subtotal).toFixed(2)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div class="flex flex-col gap-2">
					<p class="text-xs text-muted-foreground">UC-AD17 corregir nombre / UC-AD18 normalizar unidad — edite cantidad o producto_id antes de validar. Nota: el backend valida disponibilidad (publicado) y solo el creador puede editar vía PUT /orders; staff verá 403 hasta que se implemente PATCH admin.</p>
					{#each editedItems as it, idx}
						<div class="flex gap-2 items-center border p-2">
							<Input bind:value={it.product_id} placeholder="product_id UUID" class="flex-1 font-mono text-xs" />
							<Input bind:value={it.cantidad} type="number" step="0.01" placeholder="cantidad" class="w-24" />
							<span class="text-xs">${Number(it.precio_unitario).toFixed(2)}</span>
						</div>
					{/each}
					<div class="flex gap-2">
						<Button size="sm" onclick={saveEditedItems} disabled={savingEdit}>{savingEdit ? 'Guardando…' : 'Guardar items'}</Button>
						<Button size="sm" variant="outline" onclick={() => (editingItems = false)}>Cancelar</Button>
					</div>
				</div>
			{/if}
		</Card>
	{/if}
</div>

<Dialog bind:open={showReject} title="Rechazar pedido">
	<textarea bind:value={motivo} rows="3" class="w-full border bg-background px-3 py-2 text-sm" placeholder="Motivo…"></textarea>
	<div class="flex justify-end gap-2 mt-3">
		<Button variant="outline" size="sm" onclick={() => (showReject = false)}>Cancelar</Button>
		<Button variant="destructive" size="sm" onclick={reject}>Rechazar</Button>
	</div>
</Dialog>

<Dialog bind:open={showReassign} title="Reasignar pedido (RN-27, ADR-007)">
	<p class="text-xs text-muted-foreground mb-2">Solo pedidos pendientes, a vendedor activo con auditoría.</p>
	<select bind:value={toVendedor} class="w-full border bg-background px-3 py-2 text-sm h-10">
		<option value="">Seleccione vendedor destino</option>
		{#each vendedores as v}
			<option value={v.id}>{v.display_name} — {v.email}</option>
		{/each}
	</select>
	<div class="flex justify-end gap-2 mt-3">
		<Button variant="outline" size="sm" onclick={() => (showReassign = false)}>Cancelar</Button>
		<Button size="sm" onclick={reassign}>Reasignar</Button>
	</div>
</Dialog>
