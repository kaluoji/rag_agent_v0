<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { queryStore } from '$lib/stores';
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Separator } from '$lib/components/ui/separator';
	import { Markdown } from '$lib/components/prompt-kit/markdown';
	import { ArrowLeft, Share2, Copy, Calendar, FileText, CheckCircle } from 'lucide-svelte';

	// Obtener ID del parámetro de ruta
	const queryId = $derived($page.params.id ?? '');

	// Buscar la consulta en el store
	const query = $derived(queryId ? queryStore.getQueryById(queryId) : undefined);

	// Estado para feedback
	let copiedMessage = $state(false);
	let sharedMessage = $state(false);

	// Formatear fecha completa
	function formatFullDate(timestamp: string): string {
		const date = new Date(timestamp);
		return date.toLocaleString('es-ES', {
			day: '2-digit',
			month: 'long',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	// Copiar respuesta al portapapeles
	async function copyToClipboard() {
		if (!query) return;

		try {
			await navigator.clipboard.writeText(query.response);
			copiedMessage = true;
			setTimeout(() => (copiedMessage = false), 2000);
		} catch (error) {
			console.error('Error al copiar:', error);
		}
	}

	// Compartir consulta
	async function shareQuery() {
		const url = window.location.href;

		try {
			if (navigator.share) {
				await navigator.share({
					title: `Consulta: ${query?.text}`,
					url: url
				});
			} else {
				await navigator.clipboard.writeText(url);
				sharedMessage = true;
				setTimeout(() => (sharedMessage = false), 2000);
			}
		} catch (error) {
			console.error('Error al compartir:', error);
		}
	}

	// Volver al historial
	function goBack() {
		goto('/historial');
	}

	// Obtener badge para tipo
	function getTypeBadge(type: string) {
		if (type === 'gap_analysis') {
			return { label: 'Análisis GAP', variant: 'default' as const };
		}
		return { label: 'Consulta Normativa', variant: 'secondary' as const };
	}
</script>

<div class="container mx-auto p-6 max-w-4xl">
	{#if !query}
		<!-- Estado de error: consulta no encontrada -->
		<Card class="p-8 text-center">
			<FileText class="h-16 w-16 text-slate-300 mx-auto mb-4" />
			<h2 class="text-2xl font-bold text-slate-700 mb-2">Consulta no encontrada</h2>
			<p class="text-slate-500 mb-6">
				La consulta que buscas no existe o ha sido eliminada del historial.
			</p>
			<Button onclick={goBack}>
				<ArrowLeft class="h-4 w-4 mr-2" />
				Volver al historial
			</Button>
		</Card>
	{:else}
		<!-- Header sticky -->
		<div class="sticky top-0 bg-white/95 backdrop-blur-sm z-10 -mx-6 px-6 py-4 mb-6 border-b">
			<div class="flex items-center justify-between">
				<Button variant="ghost" onclick={goBack}>
					<ArrowLeft class="h-4 w-4 mr-2" />
					Volver
				</Button>

				<div class="flex gap-2">
					<Button variant="outline" onclick={copyToClipboard}>
						{#if copiedMessage}
							<CheckCircle class="h-4 w-4 mr-2 text-green-600" />
							Copiado
						{:else}
							<Copy class="h-4 w-4 mr-2" />
							Copiar
						{/if}
					</Button>

					<Button variant="outline" onclick={shareQuery}>
						<Share2 class="h-4 w-4 mr-2" />
						{sharedMessage ? 'Compartido' : 'Compartir'}
					</Button>
				</div>
			</div>
		</div>

		<!-- Metadata de la consulta -->
		<Card class="p-6 mb-6">
			<div class="flex items-start justify-between mb-4">
				<Badge variant={getTypeBadge(query.type).variant} class="text-sm">
					{getTypeBadge(query.type).label}
				</Badge>

				<div class="flex items-center gap-2 text-sm text-slate-500">
					<Calendar class="h-4 w-4" />
					{formatFullDate(query.timestamp)}
				</div>
			</div>

			<h1 class="text-2xl font-bold text-slate-900 mb-2">
				{query.text}
			</h1>

			{#if query.hasDocuments}
				<div class="flex items-center gap-2 text-sm text-blue-600 mt-3">
					<FileText class="h-4 w-4" />
					Incluye documentos adjuntos
				</div>
			{/if}
		</Card>

		<Separator class="my-6" />

		<!-- Respuesta -->
		<div class="mb-6">
			<h2 class="text-lg font-semibold text-slate-700 mb-4 flex items-center gap-2">
				<FileText class="h-5 w-5" />
				Respuesta
			</h2>

			<Card class="p-6">
				<div class="prose prose-slate max-w-none">
					<Markdown content={query.response} />
				</div>
			</Card>
		</div>

		<!-- Metadata adicional (si existe) -->
		{#if query.metadata && Object.keys(query.metadata).length > 0}
			<div class="mb-6">
				<h2 class="text-lg font-semibold text-slate-700 mb-4">Metadata</h2>
				<Card class="p-4">
					<pre class="text-xs text-slate-600 overflow-auto">{JSON.stringify(
							query.metadata,
							null,
							2
						)}</pre>
				</Card>
			</div>
		{/if}
	{/if}
</div>

<style>
	/* Estilos para markdown */
	:global(.prose) {
		color: #334155;
	}

	:global(.prose h1) {
		font-size: 1.875rem;
		font-weight: 700;
		margin-top: 1.5rem;
		margin-bottom: 1rem;
	}

	:global(.prose h2) {
		font-size: 1.5rem;
		font-weight: 600;
		margin-top: 1.25rem;
		margin-bottom: 0.75rem;
	}

	:global(.prose h3) {
		font-size: 1.25rem;
		font-weight: 600;
		margin-top: 1rem;
		margin-bottom: 0.5rem;
	}

	:global(.prose p) {
		margin-bottom: 1rem;
		line-height: 1.75;
	}

	:global(.prose ul),
	:global(.prose ol) {
		margin-bottom: 1rem;
		padding-left: 1.5rem;
	}

	:global(.prose li) {
		margin-bottom: 0.5rem;
	}

	:global(.prose code) {
		background-color: #f1f5f9;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-size: 0.875em;
		font-family: 'Courier New', monospace;
	}

	:global(.prose pre) {
		background-color: #1e293b;
		color: #e2e8f0;
		padding: 1rem;
		border-radius: 0.5rem;
		overflow-x: auto;
		margin-bottom: 1rem;
	}

	:global(.prose pre code) {
		background-color: transparent;
		padding: 0;
		color: inherit;
	}

	:global(.prose table) {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 1rem;
	}

	:global(.prose th),
	:global(.prose td) {
		border: 1px solid #e2e8f0;
		padding: 0.5rem;
		text-align: left;
	}

	:global(.prose th) {
		background-color: #f8fafc;
		font-weight: 600;
	}

	:global(.prose blockquote) {
		border-left: 4px solid #00548f;
		padding-left: 1rem;
		margin: 1rem 0;
		font-style: italic;
		color: #64748b;
	}
</style>
