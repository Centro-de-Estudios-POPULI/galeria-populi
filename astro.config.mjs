import { defineConfig } from 'astro/config';

// Si publicas en GitHub Pages bajo un repo (no dominio propio), define 'base'.
// Ej: site: 'https://populi.github.io', base: '/galeria-populi'
export default defineConfig({
  site: 'https://datos.populi.org.bo',
  // base: '/galeria-populi',
});
