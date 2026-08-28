<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Dialog from '$lib/components/ui/dialog.svelte';

	let pedidos = $state([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state(null);
	let estado = $state('pendiente');
	let searchUserId = $state('');
	let limit = 20;
	let offset = $state(0);
	let selected = $state(new Set());
	let showReject = $state(false);
	let rejectId = $state(null);
	let rejectMotivo = $state('');
	let vendedores = $state([]);
	let reassignMap = $state({}); // pedido_id -> to_vendedor_id

	const estados = [
		{ v: 'pendiente', label: 'Pendientes (UC-AD13)' },
		{ v: 'aceptado', label: 'Validados (UC-AD12)' },
		{ v: 'rechazado', label: 'Rechazados (UC-AD14)' },
		{ v: '', label: 'Todos' }
	];

	async function fetchVendedores() {
		try {
			const data = await api.get('/admin/users', { role: 'vendedor', limit: 50, offset: 0 });
			vendedores = data.items.filter((u) => u.is_active);
		} catch {
			vendedores = [];
		}
	}

	async function fetchPedidos() {
		loading = true;
		error = null;
		try {
			const params = { limit, offset };
			if (estado) params.estado = estado;
			if (searchUserId.trim()) params.user_id = searchUserId.trim();
			const data = await api.get('/admin/orders', params);
			pedidos = data.items;
			total = data.total;
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function toggleSelect(id) {
		const n = new Set(selected);
		if (n.has(id)) n.delete(id);
		else n.add(id);
		selected = n;
	}

	async function accept(id) {
		try {
			await api.post(`/admin/orders/${id}/accept`, {});
			await fetchPedidos();
		} catch (e) {
			alert('Error aceptar: ' + e.message);
		}
	}

	function openReject(id) {
		rejectId = id;
		rejectMotivo = '';
		showReject = true;
	}

	async function doReject() {
		if (!rejectMotivo.trim()) {
			alert('Motivo requerido (UC-AD16)');
			return;
		}
		try {
			await api.post(`/admin/orders/${rejectId}/reject`, { motivo_rechazo: rejectMotivo });
			showReject = false;
			await fetchPedidos();
		} catch (e) {
			alert('Error rechazar: ' + e.message);
		}
	}

	async function reassign(id) {
		const to = reassignMap[id];
		if (!to) {
			alert('Seleccione vendedor destino');
			return;
		}
		try {
			await api.patch(`/admin/orders/${id}/reassign`, { to_vendedor_id: to });
			await fetchPedidos();
		} catch (e) {
			alert('Error reasignar (RN-27): ' + e.message);
		}
	}

	async function consolidate() {
		if (selected.size < 2) {
			alert('Seleccione al menos 2 pedidos del mismo comprador (RN-29)');
			return;
		}
		try {
			const res = await api.post('/admin/orders/consolidate', { pedido_ids: Array.from(selected) });
			alert('Consolidado OK · OC ' + res.orden_compra.numero + ' total $' + res.orden_compra.total);
			selected = new Set();
			await fetchPedidos();
		} catch (e) {
			alert('Error consolidar: ' + e.message);
		}
	}

	function nextPage() {
		if (offset + limit < total) {
			offset += limit;
			fetchPedidos();
		}
	}
	function prevPage() {
		if (offset > 0) {
			offset = Math.max(0, offset - limit);
			fetchPedidos();
		}
	}

	function changeEstado(v) {
		estado = v;
		offset = 0;
		selected = new Set();
		fetchPedidos();
	}

	onMount(() => {
		// read query param estado if present
		const qp = $page.url.searchParams.get('estado');
		if (qp) estado = qp;
		const uid = $page.url.searchParams.get('user_id');
		if (uid) searchUserId = uid;
		fetchVendedores();
		fetchPedidos();
	});
</script>

<svelte:head>
	<title>Pedidos — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<div class="flex flex-col gap-2">
		<h1 class="font-oswald font-bold text-xl">Pedidos</h1>
		<p class="text-xs text-muted-foreground">UC-AD12..AD19 · RN-27 reasignar, RN-29 consolidar, estados: pendiente → aceptado/rechazado</p>
		<div class="flex flex-wrap gap-1">
			{#each estados as e}
				<button
					onclick={() => changeEstado(e.v)}
					class="px-3 py-1 text-xs font-oswald font-bold border {estado === e.v
						? 'bg-[#1a1f3a] text-white border-[#1a1f3a]'
						: 'bg-background hover:bg-accent'}"
				>
					{e.label}
				</button>
			{/each}
		</div>
	</div>

	<Card class="p-3 flex flex-col md:flex-row gap-3 items-end">
		<label class="flex flex-col gap-1 text-xs flex-1">
			<span class="font-oswald font-bold">Filtrar por user_id (comprador)</span>
			<div class="flex gap-2">
				<Input bind:value={searchUserId} placeholder="UUID comprador" class="flex-1" />
				<Button size="sm" onclick={() => { offset = 0; fetchPedidos(); }}>Filtrar</Button>
				<Button variant="outline" size="sm" onclick={() => { searchUserId = ''; offset = 0; fetchPedidos(); }}>Limpiar</Button>
			</div>
		</label>
		<div class="flex gap-2">
			<Button size="sm" variant="secondary" onclick={consolidate} disabled={selected.size < 2}>Consolidar ({selected.size})</Button>
			<Button variant="outline" size="sm" onclick={fetchPedidos}>Recargar</Button>
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
							<th class="px-2 py-2">☐</th>
							<th class="px-3 py-2">ID</th>
							<th class="px-3 py-2">Cliente</th>
							<th class="px-3 py-2">Vendedor</th>
							<th class="px-3 py-2">Estado</th>
							<th class="px-3 py-2">Total</th>
							<th class="px-3 py-2">Creado</th>
							<th class="px-3 py-2">Acciones</th>
						</tr>
					</thead>
					<tbody>
						{#each pedidos as p (p.id)}
							<tr class="border-t hover:bg-muted/50">
								<td class="px-2 py-2">
									{#if p.estado === 'pendiente'}
										<input type="checkbox" checked={selected.has(p.id)} onchange={() => toggleSelect(p.id)} />
									{/if}
								</td>
								<td class="px-3 py-2 font-mono text-xs"><a href="/pedidos/{p.id}" class="underline">{p.id.slice(0, 8)}…</a></td>
								<td class="px-3 py-2 font-mono text-xs">{p.user_id.slice(0, 8)}…</td>
								<td class="px-3 py-2 font-mono text-xs">{p.vendedor_id ? p.vendedor_id.slice(0, 8) + '…' : '—'}</td>
								<td class="px-3 py-2"><Badge variant={p.estado === 'pendiente' ? 'outline' : p.estado === 'aceptado' ? 'secondary' : 'destructive'}>{p.estado}</Badge></td>
								<td class="px-3 py-2">${Number(p.total).toFixed(2)}</td>
								<td class="px-3 py-2 text-xs">{new Date(p.created_at).toLocaleDateString()}</td>
								<td class="px-3 py-2 flex flex-wrap gap-1">
									<a href="/pedidos/{p.id}" class="border px-2 py-1 text-xs hover:bg-accent">Ver</a>
									{#if p.estado === 'pendiente'}
										<button onclick={() => accept(p.id)} class="border px-2 py-1 text-xs bg-secondary text-secondary-foreground hover:brightness-95">Aceptar</button>
										<button onclick={() => openReject(p.id)} class="border px-2 py-1 text-xs text-destructive hover:bg-accent">Rechazar</button>
										<div class="flex gap-1 items-center">
											<select bind:value={reassignMap[p.id]} class="border text-xs px-1 py-1 bg-background">
												<option value="">Reasignar a…</option>
												{#each vendedores as v}
													<option value={v.id}>{v.display_name} ({v.email})</option>
												{/each}
											</select>
											<button onclick={() => reassign(p.id)} class="border px-1 py-1 text-xs hover:bg-accent">↻</button>
										</div>
									{/if}
								</td>
							</tr>
						{/each}
						{#if pedidos.length === 0}
							<tr><td colspan="8" class="px-3 py-6 text-center text-muted-foreground">Sin pedidos en este estado</td></tr>
						{/if}
					</tbody>
				</table>
			</div>
			<div class="flex items-center justify-between p-3 border-t bg-muted/20">
				<span class="text-xs">Total: {total} · Página {Math.floor(offset / limit) + 1} de {Math.ceil(total / limit) || 1}</span>
				<div class="flex gap-2">
					<Button variant="outline" size="sm" onclick={prevPage} disabled={offset === 0}>Anterior</Button>
					<Button variant="outline" size="sm" onclick={nextPage} disabled={offset + limit >= total}>Siguiente</Button>
				</div>
			</div>
		</Card>
	{/if}
</div>

<Dialog bind:open={showReject} title="Rechazar pedido (UC-AD16)">
	<p class="text-xs text-muted-foreground mb-2">Motivo será visible para el comprador (UC-B08).</p>
	<textarea bind:value={rejectMotivo} rows="3" class="w-full border bg-background px-3 py-2 text-sm" placeholder="Motivo de rechazo…"></textarea>
	<div class="flex justify-end gap-2 mt-3">
		<Button variant="outline" size="sm" onclick={() => (showReject = false)}>Cancelar</Button>
		<Button variant="destructive" size="sm" onclick={doReject}>Rechazar</Button>
	</div>
</Dialog>
