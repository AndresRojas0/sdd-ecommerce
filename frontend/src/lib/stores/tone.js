import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const TONES = {
	classic: {
		label: 'Clásico',
		colors: ['#003087', '#ffd700', '#e85d04']
	},
	green: {
		label: 'Verde',
		colors: ['#0e7a5a', '#cbe6d3', '#e07b00']
	}
};

function createToneStore() {
	const { subscribe, set } = writable('classic');

	if (browser) {
		const saved = localStorage.getItem('tone');
		if (saved && TONES[saved]) {
			set(saved);
			document.documentElement.setAttribute('data-tone', saved);
		} else {
			document.documentElement.setAttribute('data-tone', 'classic');
		}
	}

	return {
		subscribe,
		setTone: (tone) => {
			if (!TONES[tone]) return;
			set(tone);
			if (browser) {
				document.documentElement.setAttribute('data-tone', tone);
				localStorage.setItem('tone', tone);
			}
		},
		TONES
	};
}

export const tone = createToneStore();
