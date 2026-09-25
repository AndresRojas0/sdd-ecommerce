import adapterNode from '@sveltejs/adapter-node';
import adapterVercel from '@sveltejs/adapter-vercel';

// Vercel exporta VERCEL=1 durante el build; compose/local usa adapter-node
// (el Dockerfile corre `node build`).
const adapter = process.env.VERCEL ? adapterVercel() : adapterNode();

const config = {
	kit: {
		adapter,
		alias: {
			$lib: './src/lib'
		}
	}
};

export default config;
