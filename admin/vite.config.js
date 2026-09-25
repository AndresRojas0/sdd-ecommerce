import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// Proxy del API para dev: las llamadas salen same-origin (localhost:5173) y
// las cookies de sesión son first-party — los navegadores bloquean cookies
// cross-site aunque sean SameSite=None; Secure.
// Uso contra producción:
//   VITE_API_PROXY_TARGET=https://sdd-ecommerce-1310dbf4.fastapicloud.dev npm run dev
// Default: API local del compose (localhost:8000).
const API_PROXY_TARGET = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';

const API_PREFIXES = [
	'/auth',
	'/users',
	'/admin',
	'/products',
	'/favorites',
	'/carts',
	'/orders',
	'/categorias',
	'/colecciones',
	'/etiquetas',
	'/unidades-medida',
	'/health',
	'/healthz'
];

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: Object.fromEntries(
			API_PREFIXES.map((p) => [p, { target: API_PROXY_TARGET, changeOrigin: true, secure: true }])
		)
	}
});
