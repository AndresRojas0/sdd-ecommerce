<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Dialog from '$lib/components/ui/dialog.svelte';

	const COLUMNS = [
		{ key: 'pendiente', label: 'Recibido', sublabel: 'pendiente', border: '#eab308', dot: 'bg-[#eab308]', badge: 'outline' },
		{ key: 'aceptado', label: 'En preparación', sublabel: 'aceptado', border: '#3b82f6', dot: 'bg-[#3b82f6]', badge: 'secondary' },
		{ key: 'facturado', label: 'Facturación', sublabel: 'facturado', border: '#e85d04', dot: 'bg-[#e85d04]', badge: 'secondary' },
		{ key: 'en_logistica', label: 'Logística', sublabel: 'en_logistica', border: '#7c3aed', dot: 'bg-[#7c3aed]', badge: 'outline' },
		{ key: 'entregado', label: 'Entregado', sublabel: 'entregado', border: '#16a34a', dot: 'bg-[#16a34a]', badge: 'outline' }
	];

	let columnState = $state({
		pendiente: { items: [], total: 0, sum: 0, loading: true, error: null },
		aceptado: { items: [], total: 0, sum: 0, loading: true, error: null },
		facturado: { items: [], total: 0, sum: 0, loading: true, error: null },
		en_logistica: { items: [], total: 0, sum: 0, loading: true, error: null },
		entregado: { items: [], total: 0, sum: 0, loading: true, error: null }
	});
	let rechazados = $state({ items: [], total: 0, sum: 0, loading: true, error: null, open: false });

	let searchUserId = $state('');
	let globalError = $state(null);
	let globalLoading = $state(false);
	let vendedores = $state([]);
	let reassignMap = $state({});
	let selected = $state(new Set());

	let showReject = $state(false);
	let rejectId = $state(null);
	let rejectMotivo = $state('');
	let actionLoading = $state(null); // pedido id being acted on

	function sumOf(items) {
		return items.reduce((a, p) => a + Number(p.total || 0), 0);
	}

	async function fetchVendedores() {
		try {
			const data = await api.get('/admin/users', { role: 'vendedor', limit: 50, offset: 0 });
			vendedores = (data.items || []).filter((u) => u.is_active);
		} catch {
			vendedores = [];
		}
	}

	async function fetchColumn(estado) {
		const st = columnState[estado];
		st.loading = true;
		st.error = null;
		try {
			const params = { estado, limit: 50, offset: 0 };
			if (searchUserId.trim()) params.user_id = searchUserId.trim();
			const data = await api.get('/admin/orders', params);
			st.items = data.items || [];
			st.total = data.total ?? st.items.length;
			st.sum = sumOf(st.items);
		} catch (e) {
			if (e.status === 401) st.error = 'No autenticado (401) — inicie sesión nuevamente';
			else if (e.status === 403) st.error = 'Acceso denegado (403) — rol no autorizado';
			else st.error = e.message;
			st.items = [];
		} finally {
			st.loading = false;
		}
	}

	async function fetchRechazados() {
		rechazados.loading = true;
		rechazados.error = null;
		try {
			const params = { estado: 'rechazado', limit: 50, offset: 0 };
			if (searchUserId.trim()) params.user_id = searchUserId.trim();
			const data = await api.get('/admin/orders', params);
			rechazados.items = data.items || [];
			rechazados.total = data.total ?? rechazados.items.length;
			rechazados.sum = sumOf(rechazados.items);
		} catch (e) {
			if (e.status === 401) rechazados.error = 'No autenticado (401)';
			else if (e.status === 403) rechazados.error = 'Acceso denegado (403)';
			else rechazados.error = e.message;
			rechazados.items = [];
		} finally {
			rechazados.loading = false;
		}
	}

	async function fetchAll() {
		globalLoading = true;
		globalError = null;
		try {
			await Promise.all([...COLUMNS.map((c) => fetchColumn(c.key)), fetchRechazados()]);
		} catch (e) {
			globalError = e.message;
		} finally {
			globalLoading = false;
		}
	}

	function onFilter() {
		selected = new Set();
		fetchAll();
	}
	function onClearFilter() {
		searchUserId = '';
		selected = new Set();
		fetchAll();
	}

	function shortId(id) {
		return id ? id.slice(0, 8) + '…' : '—';
	}
	function fmtDate(s) {
		if (!s) return '—';
		try {
			return new Date(s).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' });
		} catch {
			return s;
		}
	}
	function fmtMoney(n) {
		return '$' + Number(n).toFixed(2);
	}

	function toggleSelect(id) {
		const n = new Set(selected);
		if (n.has(id)) n.delete(id);
		else n.add(id);
		selected = n;
	}

	// actions
	async function doAccept(id) {
		actionLoading = id;
		try {
			await api.post(`/admin/orders/${id}/accept`, {});
			await fetchAll();
		} catch (e) {
			alert('Error aceptar: ' + e.message);
		} finally {
			actionLoading = null;
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
		actionLoading = rejectId;
		try {
			await api.post(`/admin/orders/${rejectId}/reject`, { motivo_rechazo: rejectMotivo });
			showReject = false;
			await fetchAll();
		} catch (e) {
			alert('Error rechazar: ' + e.message);
		} finally {
			actionLoading = null;
		}
	}
	async function doReassign(id) {
		const to = reassignMap[id];
		if (!to) {
			alert('Seleccione vendedor destino');
			return;
		}
		actionLoading = id;
		try {
			await api.patch(`/admin/orders/${id}/reassign`, { to_vendedor_id: to });
			await fetchColumn('pendiente');
		} catch (e) {
			alert('Error reasignar (RN-27): ' + e.message);
		} finally {
			actionLoading = null;
		}
	}
	async function doFacturar(id) {
		actionLoading = id;
		try {
			const res = await api.post(`/admin/orders/${id}/facturar`, {});
			// response contains factura + pedidos, refresh columns
			// Use non-blocking alert with factura number if present
			if (res?.factura?.numero_fiscal) {
				// toast-like via alert
				// keep subtle
			}
			await fetchAll();
		} catch (e) {
			alert('Error facturar (RN-35/RN-36): ' + e.message);
		} finally {
			actionLoading = null;
		}
	}
	async function doEnLogistica(id) {
		actionLoading = id;
		try {
			await api.post(`/admin/orders/${id}/en-logistica`, {});
			await fetchAll();
		} catch (e) {
			alert('Error pasar a logística: ' + e.message);
		} finally {
			actionLoading = null;
		}
	}
	async function doEntregar(id) {
		actionLoading = id;
		try {
			await api.post(`/admin/orders/${id}/entregar`, {});
			await fetchAll();
		} catch (e) {
			alert('Error entregar: ' + e.message);
		} finally {
			actionLoading = null;
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
			await fetchAll();
		} catch (e) {
			alert('Error consolidar: ' + e.message);
		}
	}

	onMount(() => {
		fetchVendedores();
		fetchAll();
	});
</script>

<svelte:head>
	<title>Pedidos — Kanban Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<div class="flex flex-col gap-2">
		<div class="flex flex-col md:flex-row md:items-end justify-between gap-3">
			<div>
				<h1 class="font-oswald font-bold text-xl">Pedidos — Tablero Kanban</h1>
				<p class="text-xs text-muted-foreground">5 columnas: pendiente → aceptado → facturado → en_logistica → entregado · + historial rechazados (RN-28). Stock RN-35 y factura RN-36.</p>
				<p class="text-xs text-muted-foreground">Acciones por columna con botones (MVP sin drag-and-drop). Fetches filtrados por estado.</p>
			</div>
			<div class="flex gap-2">
				<Button variant="outline" size="sm" onclick={fetchAll} disabled={globalLoading}>{globalLoading ? 'Cargando…' : 'Recargar tablero'}</Button>
			</div>
		</div>

		<Card class="p-3 flex flex-col lg:flex-row gap-3 items-end">
			<label class="flex flex-col gap-1 text-xs flex-1">
				<span class="font-oswald font-bold">Filtrar por user_id (comprador) — aplica a todas las columnas</span>
				<div class="flex gap-2">
					<Input bind:value={searchUserId} placeholder="UUID comprador" class="flex-1" />
					<Button size="sm" onclick={onFilter}>Filtrar</Button>
					<Button variant="outline" size="sm" onclick={onClearFilter}>Limpiar</Button>
				</div>
			</label>
			<div class="flex gap-2 items-center">
				<Button size="sm" variant="secondary" onclick={consolidate} disabled={selected.size < 2}>Consolidar ({selected.size})</Button>
				<span class="text-xs text-muted-foreground hidden md:inline">Solo pendientes seleccionados, mismo comprador (RN-29)</span>
			</div>
		</Card>
	</div>

	{#if globalError}
		<Alert variant="destructive"><p class="text-sm">{globalError}</p></Alert>
	{/if}

	<!-- Kanban grid: 5 columns responsive; on mobile horizontal scroll -->
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 items-start">
		{#each COLUMNS as col}
			{@const st = columnState[col.key]}
			<Card class="flex flex-col min-h-[320px] border-t-4 bg-card overflow-hidden" style="border-top-color: {col.border}">
				<div class="p-3 flex flex-col gap-1 border-b bg-card sticky top-0 z-10">
					<div class="flex items-center justify-between gap-2">
						<div class="flex items-center gap-2">
							<span class="w-2.5 h-2.5 border {col.dot} inline-block"></span>
							<h2 class="font-oswald font-bold text-sm tracking-wide">{col.label}</h2>
							<span class="text-xs font-mono text-muted-foreground">({col.sublabel})</span>
						</div>
						<Badge variant={col.badge}>{st.total}</Badge>
					</div>
					<div class="flex items-center justify-between">
						<span class="text-xs text-muted-foreground">Total: <span class="font-oswald font-bold text-foreground">{fmtMoney(st.sum)}</span></span>
						<span class="text-xs text-muted-foreground hidden xl:inline">{st.items.length} pedidos</span>
					</div>
				</div>

				<div class="flex-1 p-2 flex flex-col gap-2 overflow-auto max-h-[62vh] sm:max-h-[64vh]">
					{#if st.loading}
						<Skeleton class="h-24 w-full" />
						<Skeleton class="h-24 w-full" />
						<Skeleton class="h-24 w-full" />
					{:else if st.error}
						<Alert variant="destructive"><p class="text-xs">{st.error}</p><button onclick={() => fetchColumn(col.key)} class="text-xs underline mt-1">Reintentar</button></Alert>
					{:else if st.items.length === 0}
						<p class="text-xs text-muted-foreground text-center py-6 border border-dashed">Sin pedidos en {col.label}</p>
					{:else}
						{#each st.items as p (p.id)}
							<div class="bg-background border shadow-sm p-3 flex flex-col gap-2 text-xs">
								<div class="flex items-start justify-between gap-2">
									<a href="/pedidos/{p.id}" class="font-mono font-bold underline text-xs hover:text-primary">{shortId(p.id)}</a>
									<span class="font-oswald font-bold text-sm">{fmtMoney(p.total)}</span>
								</div>
								<div class="flex flex-col gap-0.5 text-muted-foreground">
									<span>Cliente: <span class="font-mono text-foreground">{shortId(p.user_id)}</span></span>
									<span>Vendedor: <span class="font-mono text-foreground">{p.vendedor_id ? shortId(p.vendedor_id) : '—'}</span></span>
									{#if p.orden_compra_id}
										<span>OC: <a href="/ordenes/{p.orden_compra_id}" class="font-mono underline text-foreground">{shortId(p.orden_compra_id)}</a></span>
									{/if}
									<span>{fmtDate(p.created_at)} · {p.items.length} items</span>
									{#if p.motivo_rechazo}
										<span class="text-destructive">Motivo: {p.motivo_rechazo}</span>
									{/if}
								</div>
								<div class="flex flex-wrap gap-1 pt-1 border-t mt-1">
									<a href="/pedidos/{p.id}" class="border px-2 py-1 hover:bg-accent text-xs">Ver</a>
									{#if col.key === 'pendiente'}
										<label class="flex items-center gap-1 border px-1.5 py-0.5 bg-muted/20">
											<input type="checkbox" checked={selected.has(p.id)} onchange={() => toggleSelect(p.id)} class="w-3 h-3" />
											<span class="text-xs">Sel</span>
										</label>
										<button
											onclick={() => doAccept(p.id)}
											disabled={actionLoading === p.id}
											class="border px-2 py-1 bg-[#1a1f3a] text-white hover:brightness-110 disabled:opacity-50 text-xs font-oswald font-bold"
										>
											{actionLoading === p.id ? '…' : 'Aceptar'}
										</button>
										<button onclick={() => openReject(p.id)} class="border px-2 py-1 hover:bg-accent text-destructive text-xs">Rechazar</button>
										<div class="flex gap-1 items-center w-full mt-1">
											<select bind:value={reassignMap[p.id]} class="border text-xs px-1 py-1 bg-background flex-1 min-w-0">
												<option value="">Reasignar a…</option>
												{#each vendedores as v}
													<option value={v.id}>{v.display_name} ({v.email})</option>
												{/each}
											</select>
											<button onclick={() => doReassign(p.id)} disabled={actionLoading === p.id} class="border px-2 py-1 hover:bg-accent text-xs">↻</button>
										</div>
									{/if}
									{#if col.key === 'aceptado'}
										<button
											onclick={() => doFacturar(p.id)}
											disabled={actionLoading === p.id}
											class="border px-2 py-1 bg-[#e85d04] text-white hover:brightness-110 disabled:opacity-50 text-xs font-oswald font-bold"
										>
											{actionLoading === p.id ? 'Facturando…' : 'Facturar'}
										</button>
										<button onclick={() => openReject(p.id)} class="border px-2 py-1 hover:bg-accent text-destructive text-xs">Rechazar</button>
									{/if}
									{#if col.key === 'facturado'}
										<button
											onclick={() => doEnLogistica(p.id)}
											disabled={actionLoading === p.id}
											class="border px-2 py-1 bg-[#7c3aed] text-white hover:brightness-110 disabled:opacity-50 text-xs font-oswald font-bold"
										>
											{actionLoading === p.id ? '…' : 'A Logística'}
										</button>
									{/if}
									{#if col.key === 'en_logistica'}
										<button
											onclick={() => doEntregar(p.id)}
											disabled={actionLoading === p.id}
											class="border px-2 py-1 bg-[#16a34a] text-white hover:brightness-110 disabled:opacity-50 text-xs font-oswald font-bold"
										>
											{actionLoading === p.id ? '…' : 'Entregar'}
										</button>
									{/if}
									{#if col.key === 'entregado'}
										<span class="inline-flex items-center px-2 py-1 bg-[#16a34a]/10 border border-[#16a34a]/30 text-[#16a34a] text-xs font-oswald">✓ Entregado</span>
									{/if}
								</div>
							</div>
						{/each}
					{/if}
				</div>
				<div class="p-2 border-t bg-muted/20 flex justify-between items-center">
					<span class="text-xs text-muted-foreground">{st.items.length} / {st.total}</span>
					<button onclick={() => fetchColumn(col.key)} class="text-xs underline">Actualizar</button>
				</div>
			</Card>
		{/each}
	</div>

	<!-- Rechazados history -->
	<Card class="border overflow-hidden">
		<button
			onclick={() => (rechazados.open = !rechazados.open)}
			class="w-full flex items-center justify-between p-3 bg-muted/40 hover:bg-muted/60 text-left"
		>
			<div class="flex items-center gap-2">
				<span class="w-2.5 h-2.5 bg-destructive inline-block border"></span>
				<h2 class="font-oswald font-bold text-sm">Rechazados — Historial</h2>
				<Badge variant="destructive">{rechazados.total}</Badge>
				<span class="text-xs text-muted-foreground hidden md:inline">Total: {fmtMoney(rechazados.sum)} · terminal, solo lectura</span>
			</div>
			<span class="text-xs font-oswald">{rechazados.open ? 'Ocultar ▲' : 'Ver ▼'}</span>
		</button>
		{#if rechazados.open}
			<div class="p-3 border-t">
				{#if rechazados.loading}
					<Skeleton class="h-24 w-full" />
				{:else if rechazados.error}
					<Alert variant="destructive"><p class="text-xs">{rechazados.error}</p></Alert>
				{:else if rechazados.items.length === 0}
					<p class="text-xs text-muted-foreground text-center py-4">Sin pedidos rechazados</p>
				{:else}
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-[50vh] overflow-auto">
						{#each rechazados.items as p (p.id)}
							<div class="border p-3 flex flex-col gap-1 text-xs bg-background">
								<div class="flex justify-between">
									<a href="/pedidos/{p.id}" class="font-mono font-bold underline">{shortId(p.id)}</a>
									<span class="font-oswald font-bold">{fmtMoney(p.total)}</span>
								</div>
								<span class="text-muted-foreground">Cliente: <span class="font-mono text-foreground">{shortId(p.user_id)}</span> · {fmtDate(p.created_at)}</span>
								<span class="text-muted-foreground">{p.items.length} items</span>
								{#if p.motivo_rechazo}
									<span class="text-destructive border border-destructive/20 bg-destructive/5 p-1.5">Motivo: {p.motivo_rechazo}</span>
								{/if}
								<span class="text-xs text-muted-foreground">Duplicar: acción del comprador (UC-B08), no admin.</span>
								<a href="/pedidos/{p.id}" class="border px-2 py-1 hover:bg-accent text-xs w-fit mt-1">Ver</a>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</Card>
</div>

<Dialog bind:open={showReject} title="Rechazar pedido (UC-AD16)">
	<p class="text-xs text-muted-foreground mb-2">Motivo será visible para el comprador (UC-B08). Si el pedido está aceptado, se libera la reserva de stock (RN-35 devolución).</p>
	<textarea bind:value={rejectMotivo} rows="3" class="w-full border bg-background px-3 py-2 text-sm" placeholder="Motivo de rechazo…"></textarea>
	<div class="flex justify-end gap-2 mt-3">
		<Button variant="outline" size="sm" onclick={() => (showReject = false)}>Cancelar</Button>
		<Button variant="destructive" size="sm" onclick={doReject} disabled={actionLoading === rejectId}>{actionLoading === rejectId ? 'Rechazando…' : 'Rechazar'}</Button>
	</div>
</Dialog>
