<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';

	let user = $state(null);
	let loading = $state(true);
	let error = $state(null);
	let pedidos = $state([]);
	let pedidosTotal = $state(0);
	let id = $derived($page.params.id);

	async function fetchAll() {
		loading = true;
		error = null;
		try {
			user = await api.get(`/admin/users/${id}`);
			try {
				const p = await api.get('/admin/orders', { vendedor_id: id, limit: 20, offset: 0 });
				pedidos = p.items;
				pedidosTotal = p.total;
			} catch {
				pedidos = [];
			}
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}
	onMount(fetchAll);
</script>

<svelte:head>
	<title>Vendedor {user?.email ?? id} — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<a href="/vendedores" class="text-sm underline">← Volver a vendedores</a>
	{#if loading}
		<Skeleton class="h-48 w-full" />
	{:else if error}
		<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
	{:else if user}
		<Card class="p-4 flex flex-col gap-3">
			<div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
				<div>
					<h1 class="font-oswald font-bold text-xl">{user.display_name} <span class="text-sm font-normal text-muted-foreground">vendedor</span></h1>
					<p class="text-sm font-mono">{user.email}</p>
				</div>
				<div class="flex gap-2">
					<Badge>{user.role}</Badge>
					<Badge variant={user.is_active ? 'secondary' : 'destructive'}>{user.is_active ? 'activo' : 'inactivo'}</Badge>
				</div>
			</div>
			<div class="grid grid-cols-2 gap-3 text-sm">
				<div><span class="text-muted-foreground">Creado:</span> {new Date(user.created_at).toLocaleString()}</div>
				<div><span class="text-muted-foreground">Último login:</span> {user.last_login_at ? new Date(user.last_login_at).toLocaleString() : '—'}</div>
			</div>
			<p class="text-xs text-muted-foreground">Al desactivar, sus órdenes confirmadas quedan congeladas y sus pedidos pendientes son reasignables (RN-27, ADR-007).</p>
		</Card>
		<Card class="p-4">
			<h3 class="font-oswald font-bold text-sm mb-2">Pedidos asignados ({pedidosTotal}) — UC-AD24</h3>
			{#if pedidos.length === 0}
				<p class="text-xs text-muted-foreground">Sin pedidos asignados</p>
			{:else}
				<div class="overflow-auto">
					<table class="w-full text-xs">
						<thead><tr class="border-b"><th class="text-left p-1">ID</th><th class="text-left p-1">Cliente</th><th class="text-left p-1">Estado</th><th class="text-left p-1">Total</th></tr></thead>
						<tbody>
							{#each pedidos as p}
								<tr class="border-b">
									<td class="p-1 font-mono"><a href="/pedidos/{p.id}" class="underline">{p.id.slice(0, 8)}…</a></td>
									<td class="p-1 font-mono text-xs">{p.user_id.slice(0, 8)}…</td>
									<td class="p-1"><Badge variant={p.estado === 'pendiente' ? 'outline' : p.estado === 'aceptado' ? 'secondary' : 'destructive'}>{p.estado}</Badge></td>
									<td class="p-1">${Number(p.total).toFixed(2)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</Card>
	{/if}
</div>
