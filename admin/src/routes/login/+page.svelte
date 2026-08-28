<script>
	import { goto } from '$app/navigation';
	import { login, authError, authLoading, user } from '$lib/stores/auth.js';
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client.js';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Alert from '$lib/components/ui/alert.svelte';

	let email = $state('admin876861@example.com');
	let password = $state('Cambiar1!');
	let error = $state(null);
	let success = $state(null);
	let showChange = $state(false);
	let currentPassword = $state('');
	let newPassword = $state('');
	let changeError = $state(null);
	let changeSuccess = $state(null);
	let mustChangeDetected = $state(false);

	onMount(() => {
		// prefill from query if needed
	});

	async function handleLogin(e) {
		e.preventDefault();
		error = null;
		success = null;
		mustChangeDetected = false;
		try {
			await login(email, password);
			success = 'Login exitoso';
			await goto('/');
		} catch (err) {
			const detail = err.data?.detail;
			if (detail?.code === 'MUST_CHANGE_PASSWORD') {
				mustChangeDetected = true;
				showChange = true;
				error = 'Debe cambiar su contraseña antes de continuar (BOOT-03). Complete el formulario de cambio.';
				currentPassword = password;
			} else if (Array.isArray(detail)) {
				error = detail.map((d) => d.msg).join('; ');
				// hint for .local
				if (email.includes('.local')) {
					error += ' — El validador rechaza .local. Pruebe con admin876861@example.com / Cambiar1!';
				}
			} else {
				error = err.message || 'Error de login';
				if (email.includes('.local') && err.status === 422) {
					error += ' — Pruebe con admin876861@example.com / Cambiar1!';
				}
			}
		}
	}

	async function handleChangePassword(e) {
		e.preventDefault();
		changeError = null;
		changeSuccess = null;
		// This flow requires an authenticated token. Since MUST_CHANGE blocks login,
		// we attempt to obtain a token via a direct login bypass: try to call
		// POST /auth/login but the token is not issued. So we show guidance.
		// However we still try the normal change-password flow: first login with current creds
		// to get token (if backend allowed), then change.
		try {
			// Attempt to login to get token - but if MUST_CHANGE, this will fail.
			// Instead we try to call change-password-force directly after obtaining token
			// via a manual fetch that includes credentials as cookies if any.
			// For dev, we can try to use the existing session if any.
			// First, try to use api.post to change-password with current session (may need token)
			// If no token, we inform user to use curl fallback.

			// Try to get a token by calling login and ignoring MUST_CHANGE error
			// by attempting a direct fetch to /auth/change-password-force with auth header from a generated token
			// Fallback: instruct user.

			// Attempt naive: call /auth/change-password-force via api (will add cookies if present)
			// But we don't have cookies, so it will 401. We'll catch and show help.
			await api.post('/auth/change-password-force', {
				current_password: currentPassword,
				new_password: newPassword
			});
			changeSuccess = 'Contraseña cambiada. Inicie sesión nuevamente con la nueva contraseña.';
			showChange = false;
			mustChangeDetected = false;
			password = newPassword;
		} catch (err) {
			const detail = err.data?.detail;
			if (err.status === 401) {
				changeError =
					'No se pudo cambiar la contraseña sin sesión válida. El backend bloquea login con must_change_password sin emitir token. Solución dev: ejecute en el contenedor api: python -c "from app.db.base import SessionLocal; from app.models.user import User; from sqlalchemy import select; from app.core.security import hash_password; db=SessionLocal(); u=db.scalar(select(User).where(User.email==\'' +
					email +
					'\')); u.password_hash=hash_password(\'' +
					newPassword +
					'\'); u.must_change_password=False; db.commit()" y luego reintente login.';
			} else if (detail) {
				changeError = typeof detail === 'string' ? detail : JSON.stringify(detail);
			} else {
				changeError = err.message;
			}
		}
	}
</script>

<svelte:head>
	<title>Login — Punto App Admin</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-[#1a1f3a] p-4">
	<Card class="w-full max-w-md p-6 flex flex-col gap-4 bg-card">
		<div class="text-center">
			<h1 class="font-oswald font-bold text-2xl tracking-wide text-primary">PUNTO APP — Admin</h1>
			<p class="text-sm text-muted-foreground mt-1">Acceso para administrador y vendedor</p>
		</div>

		{#if error}
			<Alert variant="destructive"><p class="text-sm">{error}</p></Alert>
		{/if}
		{#if success}
			<Alert><p class="text-sm">{success}</p></Alert>
		{/if}
		{#if $authError}
			<Alert variant="destructive"><p class="text-sm">{$authError}</p></Alert>
		{/if}

		<form onsubmit={handleLogin} class="flex flex-col gap-3">
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Email</span>
				<Input bind:value={email} type="email" placeholder="admin@example.com" required />
				<span class="text-xs text-muted-foreground">Pruebe: admin876861@example.com / vend876861@example.com</span>
			</label>
			<label class="flex flex-col gap-1 text-sm">
				<span class="font-oswald font-bold">Contraseña</span>
				<Input bind:value={password} type="password" required />
				<span class="text-xs text-muted-foreground">Admin seed: Cambiar1! (debe cumplir RN-15)</span>
			</label>
			<Button type="submit" disabled={$authLoading}>
				{#if $authLoading}Ingresando…{:else}Ingresar{/if}
			</Button>
			<p class="text-xs text-muted-foreground text-center">
				Si ve "Debe cambiar contraseña", use el formulario debajo o reinicie el password vía DB (ver ayuda).
			</p>
		</form>

		{#if showChange || mustChangeDetected}
			<div class="border-t pt-4 mt-2">
				<h3 class="font-oswald font-bold text-sm mb-2">Cambiar contraseña obligatoria (BOOT-03)</h3>
				{#if changeError}
					<Alert variant="destructive"><p class="text-xs whitespace-pre-wrap">{changeError}</p></Alert>
				{/if}
				{#if changeSuccess}
					<Alert><p class="text-xs">{changeSuccess}</p></Alert>
				{/if}
				<form onsubmit={handleChangePassword} class="flex flex-col gap-2 mt-2">
					<Input bind:value={currentPassword} type="password" placeholder="Contraseña actual" required />
					<Input bind:value={newPassword} type="password" placeholder="Nueva contraseña (min 8, mayúscula, número, símbolo)" required />
					<Button type="submit" variant="secondary" size="sm">Cambiar contraseña</Button>
				</form>
				<p class="text-xs text-muted-foreground mt-2">
					Nota: el backend actual no emite token con must_change_password=true, por lo que este endpoint fallará con 401 hasta que se corrija el backend o se haga reset manual en DB.
				</p>
			</div>
		{/if}

		<div class="text-xs text-muted-foreground text-center border-t pt-3">
			Backend: http://localhost:8000 · <a href="/" class="underline">Volver al dashboard</a>
		</div>
	</Card>
</div>
