<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Dialog from '$lib/components/ui/dialog.svelte';

	let user = $state(null);
	let loading = $state(true);
	let error = $state(null);
	let pedidos = $state([]);
	let pedidosTotal = $state(0);
	let ordenes = $state([]);
	let ordenesTotal = $state(0);
	let me = $state(null);

	// A-USR-09: cambio de rol con confirmación
	let pendingRole = $state(null);
	let showRoleConfirm = $state(false);

	// A-USR-08: reset de contraseña
	let showReset = $state(false);
	let resetTemp = $state('');
	let resetting = $state(false);
	let resetError = $state(null);

	// Contraseña temporal: se muestra UNA sola vez
	let showTemp = $state(false);
	let tempPassword = $state('');
	let tempCopied = $state(false);

	let isSelf = $derived(user && me ? user.id === me.id : false);

	let id = $derived($page.params.id);

	async function fetchAll() {
		loading = true;
		error = null;
		try {
			user = await api.get(`/admin/users/${id}`);
			try {
				me = await api.get('/admin/auth/me');
			} catch {
				me = null;
			}
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

	function onRoleSelect(e) {
		const nuevo = e.target.value;
		if (!user || nuevo === user.role) return;
		pendingRole = nuevo;
		showRoleConfirm = true;
	}

	async function confirmRoleChange() {
		if (!user || !pendingRole) return;
		try {
			user = await api.patch(`/admin/users/${user.id}/role`, { role: pendingRole });
			pendingRole = null;
			showRoleConfirm = false;
		} catch (e) {
			alert('Error: ' + e.message);
			pendingRole = null;
			showRoleConfirm = false;
			await fetchAll();
		}
	}

	function openReset() {
		resetTemp = '';
		resetError = null;
		showReset = true;
	}

	async function submitReset() {
		resetting = true;
		resetError = null;
		try {
			const body = {};
			if (resetTemp.trim()) body.temp_password = resetTemp.trim();
			const data = await api.post(`/admin/users/${user.id}/password-reset`, body);
			showReset = false;
			tempPassword = data.temp_password;
			tempCopied = false;
			showTemp = true;
			await fetchAll();
		} catch (e) {
			resetError = e.message;
		} finally {
			resetting = false;
		}
	}

	async function copyTempPassword() {
		try {
			await navigator.clipboard.writeText(tempPassword);
			tempCopied = true;
		} catch {
			// Clipboard puede fallar sin HTTPS/permiso: la contraseña sigue visible en el modal
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

		<!-- A-USR-08/09: gestión de cuenta (solo administrador) -->
		<Card class="p-4 flex flex-col md:flex-row md:items-end gap-4">
			<label class="flex flex-col gap-1 text-sm">
				Rol (A-USR-09)
				<select
					value={user.role}
					onchange={onRoleSelect}
					disabled={isSelf}
					class="border bg-background px-3 py-2 text-sm h-10 min-w-40"
				>
					{#if user.role === 'administrador'}<option value="administrador" hidden>administrador</option>{/if}
					<option value="comprador">comprador</option>
					<option value="vendedor">vendedor</option>
				</select>
				<span class="text-xs text-muted-foreground">
					{#if isSelf}
						No puede cambiar su propio rol (evitar auto-bloqueo).
					{:else}
						El panel no asigna el rol administrador; el cambio queda auditado.
					{/if}
				</span>
			</label>
			<div class="flex flex-col gap-1">
				<span class="text-sm font-medium">Contraseña (A-USR-08)</span>
				<Button variant="outline" size="sm" onclick={openReset}>Restablecer contraseña</Button>
				<span class="text-xs text-muted-foreground">Genera una temporal, revoca las sesiones activas y fuerza el cambio en el próximo login.</span>
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

<!-- A-USR-09: confirmación de cambio de rol -->
<Dialog bind:open={showRoleConfirm} title="Cambiar rol">
	<div class="flex flex-col gap-3 text-sm">
		<p>
			¿Cambiar el rol de <span class="font-mono">{user?.email}</span> de
			<strong>{user?.role}</strong> a <strong>{pendingRole}</strong>?
		</p>
		<p class="text-xs text-muted-foreground">La operación queda registrada en auditoría (usuario.cambiar_rol).</p>
		<div class="flex justify-end gap-2">
			<Button variant="outline" size="sm" onclick={() => (showRoleConfirm = false)}>Cancelar</Button>
			<Button size="sm" onclick={confirmRoleChange}>Confirmar</Button>
		</div>
	</div>
</Dialog>

<!-- A-USR-08: restablecer contraseña -->
<Dialog bind:open={showReset} title="Restablecer contraseña">
	<form
		class="flex flex-col gap-3"
		onsubmit={(e) => {
			e.preventDefault();
			submitReset();
		}}
	>
		{#if resetError}
			<Alert variant="destructive"><p class="text-sm">{resetError}</p></Alert>
		{/if}
		<p class="text-sm">
			Se generará una contraseña temporal para <span class="font-mono">{user?.email}</span>, se revocarán sus
			sesiones activas y deberá cambiarla en su próximo login.
		</p>
		<label class="flex flex-col gap-1 text-sm">
			Contraseña temporal (opcional)
			<Input type="text" bind:value={resetTemp} placeholder="vacío = generar automática" />
			<span class="text-xs text-muted-foreground">Mínimo 8 caracteres, una mayúscula, un número y un caracter especial.</span>
		</label>
		<div class="flex justify-end gap-2 mt-2">
			<Button type="button" variant="outline" size="sm" onclick={() => (showReset = false)}>Cancelar</Button>
			<Button type="submit" size="sm" disabled={resetting}>{resetting ? 'Restableciendo…' : 'Restablecer'}</Button>
		</div>
	</form>
</Dialog>

<!-- Contraseña temporal: única vez (A-USR-07/08) -->
<Dialog bind:open={showTemp} title="Contraseña temporal generada">
	<div class="flex flex-col gap-3">
		<Alert variant="destructive">
			<p class="text-sm font-semibold">No se mostrará nuevamente; el usuario deberá cambiarla en su primer login.</p>
		</Alert>
		<div class="flex items-center gap-2">
			<code class="flex-1 border bg-muted/40 px-3 py-2 font-mono text-sm break-all select-all">{tempPassword}</code>
			<Button variant="outline" size="sm" onclick={copyTempPassword}>{tempCopied ? '¡Copiada!' : 'Copiar'}</Button>
		</div>
		<p class="text-xs text-muted-foreground">
			Entregue esta contraseña al usuario por un canal seguro. En su primer login el sistema le exigirá cambiarla.
		</p>
		<div class="flex justify-end">
			<Button size="sm" onclick={() => (showTemp = false)}>Entendido</Button>
		</div>
	</div>
</Dialog>
