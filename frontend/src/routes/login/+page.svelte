<script>
	import { goto } from '$app/navigation';
	import { login, fetchMe } from '$lib/stores/auth.js';
	import Input from '$lib/components/ui/input.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Alert from '$lib/components/ui/alert.svelte';

	let email = $state('');
	let password = $state('');
	let error = $state(null);
	let loading = $state(false);

	async function handleSubmit(e) {
		e.preventDefault();
		loading = true;
		error = null;
		try {
			await login(email, password);
			await fetchMe();
			await goto('/');
		} catch (err) {
			let msg = err.message;
			if (err.data?.detail) {
				const d = err.data.detail;
				msg = typeof d === 'string' ? d : d.message || JSON.stringify(d);
				if (d.code === 'MUST_CHANGE_PASSWORD') msg = 'Debés cambiar tu contraseña antes de continuar.';
				if (d.code === 'ACCOUNT_DEACTIVATED') msg = 'Cuenta desactivada.';
			}
			error = msg;
		} finally {
			loading = false;
		}
	}
</script>

<div class="max-w-[420px] mx-auto px-4 py-12">
	<h1 class="font-oswald font-bold text-2xl mb-2">Ingresar</h1>
	<p class="text-sm text-muted-foreground mb-6">Accedé con tu email y contraseña.</p>

	{#if error}
		<Alert variant="destructive" class="mb-4"><p>{error}</p></Alert>
	{/if}

	<form onsubmit={handleSubmit} class="flex flex-col gap-4 border p-6 bg-card shadow-offset-black">
		<label class="flex flex-col gap-1 text-sm">
			Email
			<Input type="email" bind:value={email} required placeholder="vos@ejemplo.com" />
		</label>
		<label class="flex flex-col gap-1 text-sm">
			Contraseña
			<Input type="password" bind:value={password} required placeholder="••••••••" />
		</label>
		<Button type="submit" disabled={loading}>{loading ? 'Ingresando…' : 'Ingresar'}</Button>
		<p class="text-xs text-center text-muted-foreground">
			¿No tenés cuenta? <a href="/registro" class="underline font-bold">Registrate</a>
		</p>
	</form>
</div>
