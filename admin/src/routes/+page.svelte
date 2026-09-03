<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Button from '$lib/components/ui/button.svelte';

	let loading = $state(true);
	let error = $state(null);
	let stats = $state({ usuarios: null, productos: null, pedidosPendientes: null, ordenes: null, categorias: null });
	let totalesHoy = $state({ fecha: null, total: null, cantidad_facturas: null, loading: true, error: null });

	async function fetchStats() {
		loading = true;
		error = null;
		totalesHoy.loading = true;
		totalesHoy.error = null;
		try {
			const results = await Promise.allSettled([
				api.get('/admin/users', { limit: 1, offset: 0 }),
				api.get('/products', { limit: 1, offset: 0, include_hidden: true }),
				api.get('/admin/orders', { estado: 'pendiente', limit: 1, offset: 0 }),
				api.get('/admin/purchase-orders', { limit: 1, offset: 0 }),
				api.get('/categorias'),
				api.get('/admin/dashboard/totales-hoy')
			]);
			stats.usuarios = results[0].status === 'fulfilled' ? results[0].value.total : '—';
			stats.productos = results[1].status === 'fulfilled' ? results[1].value.total : '—';
			stats.pedidosPendientes = results[2].status === 'fulfilled' ? results[2].value.total : '—';
			stats.ordenes = results[3].status === 'fulfilled' ? results[3].value.total : '—';
			stats.categorias = results[4].status === 'fulfilled' ? results[4].value.length : '—';
			// if usuarios failed due to role (vendedor), try to show message
			if (results[0].status === 'rejected') {
				const e = results[0].reason;
				if (e.status === 403) stats.usuarios = 'solo admin';
			}
			if (results[5].status === 'fulfilled') {
				totalesHoy.fecha = results[5].value.fecha;
				totalesHoy.total = results[5].value.total;
				totalesHoy.cantidad_facturas = results[5].value.cantidad_facturas;
				totalesHoy.error = null;
			} else {
				const e = results[5].reason;
				if (e?.status === 401) totalesHoy.error = 'No autenticado (401)';
				else if (e?.status === 403) totalesHoy.error = 'Acceso denegado (403)';
				else totalesHoy.error = e?.message || 'Error totales';
				totalesHoy.total = null;
			}
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
			totalesHoy.loading = false;
		}
	}

	onMount(fetchStats);
</script>

<svelte:head>
	<title>Dashboard — Punto App Admin</title>
</svelte:head>

<div class="flex flex-col gap-6">
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
		<div>
			<h1 class="font-oswald font-bold text-2xl tracking-wide">Dashboard</h1>
			<p class="text-sm text-muted-foreground">Resumen operativo — UC-AD01..AD24</p>
		</div>
		<Button variant="outline" size="sm" onclick={fetchStats}>Actualizar</Button>
	</div>

	{#if error}
		<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
	{/if}

	<!-- Totales del día — RN-37 UC-AD28 -->
	<Card class="p-4 flex flex-col gap-1 border-l-4 border-l-[#16a34a] bg-gradient-to-r from-[#16a34a]/[0.06] to-transparent">
		{#if totalesHoy.loading}
			<Skeleton class="h-16 w-full" />
		{:else if totalesHoy.error}
			<span class="text-xs font-oswald font-bold tracking-wide text-muted-foreground">FACTURACIÓN HOY</span>
			<span class="text-xs text-destructive">{totalesHoy.error}</span>
			<button onclick={fetchStats} class="text-xs underline w-fit">Reintentar</button>
		{:else}
			<span class="text-xs font-oswald font-bold tracking-wide text-muted-foreground">FACTURACIÓN HOY — {totalesHoy.fecha || '—'}</span>
			<span class="font-oswald font-bold text-3xl">${totalesHoy.total != null ? Number(totalesHoy.total).toFixed(2) : '0.00'}</span>
			<span class="text-xs text-muted-foreground">{totalesHoy.cantidad_facturas ?? 0} factura(s) · RN-37 · solo facturas del día cuentan</span>
			<a href="/pedidos" class="text-xs underline mt-1">Ver kanban →</a>
		{/if}
	</Card>

	{#if loading}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
			{#each Array(4) as _}
				<Skeleton class="h-28 w-full" />
			{/each}
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
			<Card class="p-4 flex flex-col gap-1 border-l-4 border-l-[#003087]">
				<span class="text-xs font-oswald font-bold tracking-wide text-muted-foreground">USUARIOS TOTALES</span>
				<span class="font-oswald font-bold text-3xl">{stats.usuarios}</span>
				<a href="/usuarios" class="text-xs underline mt-1">Ver usuarios →</a>
			</Card>
			<Card class="p-4 flex flex-col gap-1 border-l-4 border-l-[#e85d04]">
				<span class="text-xs font-oswald font-bold tracking-wide text-muted-foreground">PRODUCTOS</span>
				<span class="font-oswald font-bold text-3xl">{stats.productos}</span>
				<span class="text-xs text-muted-foreground">incluye ocultos (include_hidden)</span>
				<a href="/productos" class="text-xs underline">Ver catálogo →</a>
			</Card>
			<Card class="p-4 flex flex-col gap-1 border-l-4 border-l-[#ffd700]">
				<span class="text-xs font-oswald font-bold tracking-wide text-muted-foreground">PEDIDOS PENDIENTES</span>
				<span class="font-oswald font-bold text-3xl">{stats.pedidosPendientes}</span>
				<a href="/pedidos?estado=pendiente" class="text-xs underline">Cola operativa →</a>
			</Card>
			<Card class="p-4 flex flex-col gap-1 border-l-4 border-l-[#1a1f3a]">
				<span class="text-xs font-oswald font-bold tracking-wide text-muted-foreground">ÓRDENES DE COMPRA</span>
				<span class="font-oswald font-bold text-3xl">{stats.ordenes}</span>
				<a href="/ordenes" class="text-xs underline">Ver órdenes →</a>
			</Card>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
			<Card class="p-4">
				<h3 class="font-oswald font-bold text-sm mb-2">Accesos rápidos</h3>
				<div class="flex flex-wrap gap-2">
					<a href="/productos/nuevo" class="bg-primary text-primary-foreground px-3 py-1.5 text-sm font-oswald font-bold border shadow-offset-navy">+ Nuevo producto</a>
					<a href="/pedidos" class="bg-secondary text-secondary-foreground px-3 py-1.5 text-sm font-oswald font-bold border shadow-offset-orange">Gestionar pedidos</a>
					<a href="/usuarios" class="border px-3 py-1.5 text-sm font-oswald">Usuarios</a>
					<a href="/vendedores" class="border px-3 py-1.5 text-sm font-oswald">Vendedores</a>
				</div>
				<p class="text-xs text-muted-foreground mt-3">Categorías registradas: {stats.categorias}</p>
			</Card>
			<Card class="p-4">
				<h3 class="font-oswald font-bold text-sm mb-2">Notas</h3>
				<ul class="text-xs text-muted-foreground list-disc pl-4 flex flex-col gap-1">
					<li>Admin bootstrap: ADMIN_INITIAL_USER / Cambiar1! con must_change_password (ADR-006, BOOT-03)</li>
					<li>Pedidos pendientes reasignables (RN-27, ADR-007) · Consolidación mismo comprador (RN-29)</li>
					<li>Productos: ocultar (RN-31) vs borrado lógico (RN-32)</li>
				</ul>
			</Card>
		</div>
	{/if}
</div>
