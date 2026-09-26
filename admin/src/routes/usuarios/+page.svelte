<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import Input from '$lib/components/ui/input.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';
	import Dialog from '$lib/components/ui/dialog.svelte';

	let users = $state([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state(null);
	let search = $state('');
	let limit = 20;
	let offset = $state(0);
	let debounceTimer;

	// A-USR-07: alta de usuario desde el panel
	let showCreate = $state(false);
	let form = $state({ email: '', display_name: '', role: 'vendedor', temp_password: '' });
	let creating = $state(false);
	let createError = $state(null);

	// Contraseña temporal: se muestra UNA sola vez tras crear
	let showTemp = $state(false);
	let tempPassword = $state('');
	let tempCopied = $state(false);

	let filtered = $derived(
		search.trim()
			? users.filter(
					(u) =>
						u.email.toLowerCase().includes(search.toLowerCase()) ||
						(u.display_name || '').toLowerCase().includes(search.toLowerCase())
				)
			: users
	);

	async function fetchUsers() {
		loading = true;
		error = null;
		try {
			const data = await api.get('/admin/users', { limit, offset });
			users = data.items;
			total = data.total;
		} catch (e) {
			error = e.message;
			if (e.status === 403) error = 'No autorizado: se requiere rol administrador';
		} finally {
			loading = false;
		}
	}

	function onSearchInput(e) {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			search = e.target.value;
		}, 300);
	}

	async function toggleActive(u) {
		try {
			if (u.is_active) {
				await api.patch(`/admin/users/${u.id}/deactivate`);
			} else {
				await api.patch(`/admin/users/${u.id}/activate`);
			}
			await fetchUsers();
		} catch (e) {
			alert('Error: ' + e.message);
		}
	}

	function openCreate() {
		form = { email: '', display_name: '', role: 'vendedor', temp_password: '' };
		createError = null;
		showCreate = true;
	}

	async function submitCreate() {
		creating = true;
		createError = null;
		try {
			const body = {
				email: form.email.trim(),
				display_name: form.display_name.trim(),
				role: form.role
			};
			if (form.temp_password.trim()) body.temp_password = form.temp_password.trim();
			const data = await api.post('/admin/users', body);
			showCreate = false;
			tempPassword = data.temp_password;
			tempCopied = false;
			showTemp = true;
			await fetchUsers();
		} catch (e) {
			createError = e.message;
		} finally {
			creating = false;
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

	function nextPage() {
		if (offset + limit < total) {
			offset += limit;
			fetchUsers();
		}
	}
	function prevPage() {
		if (offset > 0) {
			offset = Math.max(0, offset - limit);
			fetchUsers();
		}
	}

	onMount(fetchUsers);
</script>

<svelte:head>
	<title>Usuarios — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
		<div>
			<h1 class="font-oswald font-bold text-xl">Usuarios</h1>
			<p class="text-xs text-muted-foreground">UC-AD01..AD05 · Listar, buscar, activar/desactivar, métricas · Alta A-USR-07</p>
		</div>
		<div class="flex gap-2">
			<Button variant="outline" size="sm" onclick={fetchUsers}>Recargar</Button>
			<Button size="sm" onclick={openCreate}>Nuevo usuario</Button>
		</div>
	</div>

	<Card class="p-3 flex flex-col md:flex-row gap-3 items-center">
		<Input placeholder="Buscar por email o display_name…" oninput={onSearchInput} class="max-w-sm" />
		<span class="text-xs text-muted-foreground">Total: {total} · Mostrando {users.length} · Offset {offset}</span>
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
							<th class="px-3 py-2">Email</th>
							<th class="px-3 py-2">Nombre</th>
							<th class="px-3 py-2">Rol</th>
							<th class="px-3 py-2">Activo</th>
							<th class="px-3 py-2">Creado</th>
							<th class="px-3 py-2">Último login</th>
							<th class="px-3 py-2">Acciones</th>
						</tr>
					</thead>
					<tbody>
						{#each filtered as u (u.id)}
							<tr class="border-t hover:bg-muted/50">
								<td class="px-3 py-2 font-mono text-xs">{u.email}</td>
								<td class="px-3 py-2">{u.display_name}</td>
								<td class="px-3 py-2"><Badge variant={u.role === 'administrador' ? 'default' : u.role === 'vendedor' ? 'secondary' : 'outline'}>{u.role}</Badge></td>
								<td class="px-3 py-2">
									<Badge variant={u.is_active ? 'secondary' : 'destructive'}>{u.is_active ? 'activo' : 'inactivo'}</Badge>
								</td>
								<td class="px-3 py-2 text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
								<td class="px-3 py-2 text-xs">{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : '—'}</td>
								<td class="px-3 py-2 flex flex-wrap gap-1">
									<a href="/usuarios/{u.id}" class="border px-2 py-1 text-xs hover:bg-accent">Ver</a>
									<button onclick={() => toggleActive(u)} class="border px-2 py-1 text-xs hover:bg-accent {u.is_active ? 'text-destructive' : 'text-primary'}">
										{u.is_active ? 'Desactivar' : 'Activar'}
									</button>
								</td>
							</tr>
						{/each}
						{#if filtered.length === 0}
							<tr><td colspan="7" class="px-3 py-6 text-center text-muted-foreground">Sin resultados</td></tr>
						{/if}
					</tbody>
				</table>
			</div>
			<div class="flex items-center justify-between p-3 border-t bg-muted/20">
				<span class="text-xs">Página {Math.floor(offset / limit) + 1} de {Math.ceil(total / limit) || 1}</span>
				<div class="flex gap-2">
					<Button variant="outline" size="sm" onclick={prevPage} disabled={offset === 0}>Anterior</Button>
					<Button variant="outline" size="sm" onclick={nextPage} disabled={offset + limit >= total}>Siguiente</Button>
				</div>
			</div>
		</Card>
	{/if}
</div>

<!-- A-USR-07: alta de usuario (solo comprador/vendedor; no se crean administradores) -->
<Dialog bind:open={showCreate} title="Nuevo usuario">
	<form
		class="flex flex-col gap-3"
		onsubmit={(e) => {
			e.preventDefault();
			submitCreate();
		}}
	>
		{#if createError}
			<Alert variant="destructive"><p class="text-sm">{createError}</p></Alert>
		{/if}
		<label class="flex flex-col gap-1 text-sm">
			Email
			<Input type="email" required bind:value={form.email} placeholder="usuario@dominio.com" />
		</label>
		<label class="flex flex-col gap-1 text-sm">
			Nombre
			<Input required bind:value={form.display_name} placeholder="Nombre visible" maxlength="100" />
		</label>
		<label class="flex flex-col gap-1 text-sm">
			Rol
			<select bind:value={form.role} class="border bg-background px-3 py-2 text-sm h-10">
				<option value="comprador">comprador</option>
				<option value="vendedor">vendedor</option>
			</select>
			<span class="text-xs text-muted-foreground">El panel no crea administradores: el bootstrap por env es el único camino.</span>
		</label>
		<label class="flex flex-col gap-1 text-sm">
			Contraseña temporal (opcional)
			<Input type="text" bind:value={form.temp_password} placeholder="vacío = generar automática" />
			<span class="text-xs text-muted-foreground">Mínimo 8 caracteres, una mayúscula, un número y un caracter especial.</span>
		</label>
		<div class="flex justify-end gap-2 mt-2">
			<Button type="button" variant="outline" size="sm" onclick={() => (showCreate = false)}>Cancelar</Button>
			<Button type="submit" size="sm" disabled={creating}>{creating ? 'Creando…' : 'Crear usuario'}</Button>
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
