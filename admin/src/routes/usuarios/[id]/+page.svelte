<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Button from '$lib/components/ui/button.svelte';

	let user = $state(null);
	let loading = $state(true);
	let error = $state(null);
	let pedidos = $state([]);
	let pedidosTotal = $state(0);
	let ordenes = $state([]);
	let ordenesTotal = $state(0);

	let id = $derived($page.params.id);

	async function fetchAll() {
		loading = true;
		error = null;
		try {
			user = await api.get(`/admin/users/${id}`);
			// fetch pedidos for this user
			try {
				const p = await api.get('/admin/orders', { user_id: id, limit: 20, offset: 0 });
				pedidos = p.items;
				pedidosTotal = p.total;
			} catch (e) {
				// vendedor can still view user but not list orders?
				pedidos = [];
			}
			try {
				const o = await api.get('/admin/purchase-orders', { limit: 20, offset: 0 });
				// filter client side pedidos linked? Actually purchase orders don't filter by user, so show count
				ordenes = o.items.slice(0, 5);
				ordenesTotal = o.total;
			} catch {}
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	onMount(fetchAll);
</script>

<svelte:head>
	<title>Usuario {user?.email ?? id} — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<a href="/usuarios" class="text-sm underline">← Volver a usuarios</a>

	{#if loading}
		<Skeleton class="h-48 w-full" />
	{:else if error}
		<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
	{:else if user}
		<Card class="p-4 flex flex-col gap-3">
			<div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
				<div>
					<h1 class="font-oswald font-bold text-xl">{user.display_name}</h1>
					<p class="text-sm font-mono">{user.email}</p>
				</div>
				<div class="flex gap-2">
					<Badge variant={user.role === 'administrador' ? 'default' : 'secondary'}>{user.role}</Badge>
					<Badge variant={user.is_active ? 'secondary' : 'destructive'}>{user.is_active ? 'activo' : 'inactivo'}</Badge>
					{#if user.must_change_password}<Badge variant="destructive">must_change_password</Badge>{/if}
				</div>
			</div>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
				<div><span class="text-muted-foreground">Creado:</span> {new Date(user.created_at).toLocaleString()}</div>
				<div><span class="text-muted-foreground">Último login:</span> {user.last_login_at ? new Date(user.last_login_at).toLocaleString() : '—'}</div>
				<div><span class="text-muted-foreground">ID:</span> <span class="font-mono text-xs break-all">{user.id}</span></div>
				<div><span class="text-muted-foreground">Avatar:</span> {user.avatar ?? '—'}</div>
			</div>
		</Card>

		<div class="grid md:grid-cols-2 gap-4">
			<Card class="p-4">
				<h3 class="font-oswald font-bold text-sm mb-2">Pedidos del usuario ({pedidosTotal}) — UC-AD05</h3>
				{#if pedidos.length === 0}
					<p class="text-xs text-muted-foreground">Sin pedidos o sin permiso (vendedor puede ver si es su propio rol)</p>
				{:else}
					<div class="overflow-auto">
						<table class="w-full text-xs">
							<thead><tr class="border-b"><th class="text-left p-1">ID</th><th class="text-left p-1">Estado</th><th class="text-left p-1">Total</th><th class="text-left p-1">Fecha</th></tr></thead>
							<tbody>
								{#each pedidos as p}
									<tr class="border-b">
										<td class="p-1 font-mono"><a href="/pedidos/{p.id}" class="underline">{p.id.slice(0, 8)}…</a></td>
										<td class="p-1"><Badge variant={p.estado === 'pendiente' ? 'outline' : p.estado === 'aceptado' ? 'secondary' : 'destructive'}>{p.estado}</Badge></td>
										<td class="p-1">${Number(p.total).toFixed(2)}</td>
										<td class="p-1">{new Date(p.created_at).toLocaleDateString()}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
					<a href="/pedidos?user_id={id}" class="text-xs underline mt-2 inline-block">Ver todos los pedidos de este usuario →</a>
				{/if}
			</Card>
			<Card class="p-4">
				<h3 class="font-oswald font-bold text-sm mb-2">Órdenes de compra (muestra {ordenes.length} de {ordenesTotal})</h3>
				{#if ordenes.length === 0}
					<p class="text-xs text-muted-foreground">Sin órdenes</p>
				{:else}
					<ul class="text-xs flex flex-col gap-1">
						{#each ordenes as oc}
							<li class="flex justify-between border-b py-1"><a href="/ordenes/{oc.id}" class="underline font-mono">{oc.numero}</a><span>${Number(oc.total).toFixed(2)}</span></li>
						{/each}
					</ul>
				{/if}
			</Card>
		</div>
	{/if}
</div>
