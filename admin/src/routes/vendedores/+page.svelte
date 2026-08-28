<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import Input from '$lib/components/ui/input.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Alert from '$lib/components/ui/alert.svelte';
	import Skeleton from '$lib/components/ui/skeleton.svelte';

	let users = $state([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state(null);
	let search = $state('');
	let limit = 20;
	let offset = $state(0);
	let debounceTimer;

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
			const data = await api.get('/admin/users', { role: 'vendedor', limit, offset });
			users = data.items;
			total = data.total;
		} catch (e) {
			error = e.message;
			if (e.status === 403) error = 'Solo administrador puede listar usuarios (UC-AD20)';
		} finally {
			loading = false;
		}
	}

	function onSearchInput(e) {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => (search = e.target.value), 300);
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
	<title>Vendedores — Admin</title>
</svelte:head>

<div class="flex flex-col gap-4">
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
		<div>
			<h1 class="font-oswald font-bold text-xl">Vendedores</h1>
			<p class="text-xs text-muted-foreground">UC-AD20..AD24 · filtrado role=vendedor · activar/desactivar (RN-27, ADR-007)</p>
		</div>
		<Button variant="outline" size="sm" onclick={fetchUsers}>Recargar</Button>
	</div>

	<Card class="p-3 flex flex-col md:flex-row gap-3 items-center">
		<Input placeholder="Buscar vendedor por email o nombre…" oninput={onSearchInput} class="max-w-sm" />
		<span class="text-xs text-muted-foreground">Total vendedores: {total}</span>
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
								<td class="px-3 py-2"><Badge variant={u.is_active ? 'secondary' : 'destructive'}>{u.is_active ? 'activo' : 'inactivo'}</Badge></td>
								<td class="px-3 py-2 text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
								<td class="px-3 py-2 text-xs">{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : '—'}</td>
								<td class="px-3 py-2 flex flex-wrap gap-1">
									<a href="/vendedores/{u.id}" class="border px-2 py-1 text-xs hover:bg-accent">Ver</a>
									<button onclick={() => toggleActive(u)} class="border px-2 py-1 text-xs hover:bg-accent {u.is_active ? 'text-destructive' : 'text-primary'}">
										{u.is_active ? 'Desactivar' : 'Activar'}
									</button>
								</td>
							</tr>
						{/each}
						{#if filtered.length === 0}
							<tr><td colspan="6" class="px-3 py-6 text-center text-muted-foreground">Sin vendedores</td></tr>
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
