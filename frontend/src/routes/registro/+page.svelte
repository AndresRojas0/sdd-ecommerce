<script>
	import { goto } from '$app/navigation';
	import { register, login } from '$lib/stores/auth.js';
	import Input from '$lib/components/ui/input.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Alert from '$lib/components/ui/alert.svelte';

	let email = $state('');
	let display_name = $state('');
	let password = $state('');
	let error = $state(null);
	let loading = $state(false);

	async function handleSubmit(e) {
		e.preventDefault();
		loading = true;
		error = null;
		try {
			await register({ email, display_name, password });
			// auto-login
			await login(email, password);
			await goto('/');
		} catch (err) {
			let msg = err.message;
			if (err.data?.detail) {
				const d = err.data.detail;
				msg = typeof d === 'string' ? d : Array.isArray(d) ? d.map((x) => x.msg || JSON.stringify(x)).join(', ') : d.message || JSON.stringify(d);
			}
			error = msg;
		} finally {
			loading = false;
		}
	}
</script>

<div class="max-w-[420px] mx-auto px-4 py-12">
	<h1 class="font-oswald font-bold text-2xl mb-2">Crear cuenta</h1>
	<p class="text-sm text-muted-foreground mb-6">Mínimo 8 caracteres, 1 mayúscula, 1 número y 1 símbolo.</p>

	{#if error}
		<Alert variant="destructive" class="mb-4"><p>{error}</p></Alert>
	{/if}

	<form onsubmit={handleSubmit} class="flex flex-col gap-4 border p-6 bg-card shadow-offset-black">
		<label class="flex flex-col gap-1 text-sm">
			Email
			<Input type="email" bind:value={email} required placeholder="vos@ejemplo.com" />
		</label>
		<label class="flex flex-col gap-1 text-sm">
			Nombre visible
			<Input bind:value={display_name} required placeholder="Tu nombre" />
		</label>
		<label class="flex flex-col gap-1 text-sm">
			Contraseña
			<Input type="password" bind:value={password} required placeholder="••••••••" />
		</label>
		<Button type="submit" disabled={loading}>{loading ? 'Creando…' : 'Registrarme'}</Button>
		<p class="text-xs text-center text-muted-foreground">
			¿Ya tenés cuenta? <a href="/login" class="underline font-bold">Ingresar</a>
		</p>
	</form>
</div>
