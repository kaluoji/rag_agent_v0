<script lang="ts">
	import {
		Artifact,
		ArtifactAction,
		ArtifactActions,
		ArtifactContent,
		ArtifactDescription,
		ArtifactHeader,
		ArtifactTitle,
		ArtifactClose
	} from '$lib/components/ai-elements/artifact';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import * as Progress from '$lib/components/ui/progress';
	import { Loader } from '$lib/components/prompt-kit/loader';
	import { reportStore } from '$lib/stores';
	import { downloadReport, getReportHtml } from '$lib/api/report';
	import {
		Download,
		RefreshCw,
		FileText,
		AlertCircle,
		CheckCircle2
	} from 'lucide-svelte';
	import { onDestroy } from 'svelte';

	// Estado local
	let isDownloading = $state(false);
	let downloadError = $state<string | null>(null);
	let htmlContent = $state('');
	let isLoadingHtml = $state(false);
	let scrollbarWidth = 0;
	
	$effect(() => {
		if (reportStore.showPreview) {
			// Bloquear scroll del body para evitar reflow
			document.body.style.overflowY = 'scroll';
			document.body.style.paddingRight = '0px';
		}
		return () => {
			// Revertir cuando se cierre
			document.body.style.overflowY = '';
			document.body.style.paddingRight = '';
		};
	});


	// Cargar HTML cuando esté listo
	$effect(() => {
		if (reportStore.status === 'ready' && reportStore.reportId && !htmlContent) {
			// Si ya está en el store, usarlo
			if (reportStore.reportHtml) {
				htmlContent = reportStore.reportHtml;
			} else {
				loadReportHtml();
			}
		}
	});

	async function loadReportHtml() {
		if (!reportStore.reportId) return;

		try {
			isLoadingHtml = true;
			const html = await getReportHtml(reportStore.reportId);
			htmlContent = html;
		} catch (error) {
			console.error('Error al cargar HTML:', error);
		} finally {
			isLoadingHtml = false;
		}
	}

	async function handleDownload() {
		if (!reportStore.reportId) return;

		try {
			isDownloading = true;
			downloadError = null;
			await downloadReport(reportStore.reportId);
		} catch (error) {
			downloadError =
				error instanceof Error ? error.message : 'Error al descargar el reporte';
			console.error('Error al descargar:', error);
		} finally {
			isDownloading = false;
		}
	}

	function handleClose() {
		reportStore.closePreview();
		htmlContent = '';
	}

	function handleRegenerateClick() {
		reportStore.reset();
	}

	// Formatear tiempo de última actualización
	function getLastUpdated(): string {
		if (reportStore.status === 'generating') {
			return 'Generando...';
		}
		if (reportStore.status === 'ready') {
			return 'Completado hace unos momentos';
		}
		return '';
	}

	// Limpiar al desmontar
	onDestroy(() => {
		htmlContent = '';
	});
</script>

{#if reportStore.showPreview}
	<!-- Overlay -->
	<div
		class="artifact-overlay"
		onclick={handleClose}
		role="button"
		tabindex="-1"
		aria-label="Cerrar artifact"
	></div>

	<!-- Panel del artifact -->
	<div
		class="artifact-panel"
		role="dialog"
		aria-modal="true"
	>
		<Artifact class="h-full flex flex-col">
			<ArtifactHeader>
				<div class="flex-1">
					<ArtifactTitle>
						<div class="flex items-center gap-2">
							<FileText class="h-5 w-5 text-[#00548F]" />
							<span>
								{reportStore.filename || 'Reporte Normativo'}
							</span>
						</div>
					</ArtifactTitle>
					<ArtifactDescription>
						{getLastUpdated()}
					</ArtifactDescription>
				</div>
				<ArtifactActions>
					{#if reportStore.status === 'ready'}
						<ArtifactAction
							icon={Download}
							label="Descargar"
							tooltip="Descargar documento Word"
							onclick={handleDownload}
							disabled={isDownloading}
							class={isDownloading ? 'opacity-50' : ''}
						/>

						<ArtifactAction
							icon={RefreshCw}
							label="Regenerar"
							tooltip="Regenerar reporte"
							onclick={handleRegenerateClick}
						/>
					{/if}

					<ArtifactClose onclick={handleClose} />
				</ArtifactActions>
			</ArtifactHeader>

			<ArtifactContent class="flex-1 overflow-y-auto p-6">
				{#if reportStore.status === 'generating'}
					<div class="space-y-4">
						<div class="flex items-center justify-center py-8">
							<Loader variant="dots" size="lg" text="Generando reporte..." />
						</div>

						{#if reportStore.progress > 0}
							<div class="space-y-2">
								<div class="flex justify-between text-sm text-slate-600">
									<span>Progreso</span>
									<span>{reportStore.progress}%</span>
								</div>
								<Progress.Root value={reportStore.progress} class="h-2">
									<Progress.Indicator
										class="h-full bg-[#00548F] transition-all"
										style="width: {reportStore.progress}%"
									/>
								</Progress.Root>
							</div>
						{/if}

						<Alert>
							<AlertDescription class="text-sm">
								Estamos generando tu reporte basado en la consulta normativa. Este proceso
								puede tomar algunos segundos...
							</AlertDescription>
						</Alert>
					</div>
				{:else if reportStore.status === 'error'}
					<Alert variant="destructive">
						<AlertCircle class="h-4 w-4" />
						<AlertDescription>
							<p class="font-semibold">Error al generar el reporte</p>
							<p class="text-sm mt-1">{reportStore.errorMessage}</p>
						</AlertDescription>
					</Alert>
				{:else if reportStore.status === 'ready'}
					<div class="space-y-4">
						{#if downloadError}
							<Alert variant="destructive">
								<AlertCircle class="h-4 w-4" />
								<AlertDescription>
									{downloadError}
								</AlertDescription>
							</Alert>
						{/if}

						<Alert class="bg-green-50 border-green-200">
							<CheckCircle2 class="h-4 w-4 text-green-600" />
							<AlertDescription class="text-green-800">
								<p class="font-semibold">Reporte generado exitosamente</p>
								<p class="text-sm mt-1">
									El documento está listo para descargar. Vista previa debajo.
								</p>
							</AlertDescription>
						</Alert>

						{#if isLoadingHtml}
							<div class="flex items-center justify-center py-8">
								<Loader variant="dots" text="Cargando previsualización..." />
							</div>
						{:else if htmlContent}
							<!-- Preview del documento -->
							<div class="prose prose-sm max-w-none">
								<div class="document-preview bg-white border rounded-lg p-6 shadow-sm">
									{@html htmlContent}
								</div>
							</div>
						{:else}
							<Alert>
								<FileText class="h-4 w-4" />
								<AlertDescription>
									No se pudo cargar la previsualización. Puedes descargar el documento
									directamente.
								</AlertDescription>
							</Alert>
						{/if}
					</div>
				{/if}
			</ArtifactContent>
		</Artifact>
	</div>
{/if}

<style>
	/* Overlay sobre todo el contenido */
	.artifact-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.2);
		pointer-events: auto;
		z-index: 50;
		will-change: opacity;
	}

	/* En mobile también cubre todo (lo dejamos igual por claridad) */
	@media (max-width: 1023px) {
		.artifact-overlay {
			left: 0;
		}
	}

	/* Panel del artifact */
	.artifact-panel {
		position: fixed;
		top: 0;
		right: 0;
		bottom: 0;
		width: 100%;
		max-width: 500px;
		background-color: white;
		box-shadow: -4px 0 24px rgba(0, 0, 0, 0.15);
		border-left: 1px solid #e2e8f0;
		display: flex;
		flex-direction: column;
		pointer-events: auto;
		z-index: 51;
		will-change: transform;
	}

	@media (min-width: 1280px) {
		.artifact-panel {
			max-width: 550px;
		}
	}

	/* Estilos para el contenido HTML del documento */
	:global(.document-preview) {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
		line-height: 1.6;
		color: #333;
	}

	:global(.document-preview h1) {
		font-size: 1.5rem;
		font-weight: 700;
		margin-top: 1.5rem;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}

	:global(.document-preview h2) {
		font-size: 1.25rem;
		font-weight: 600;
		margin-top: 1.25rem;
		margin-bottom: 0.75rem;
		color: #2a2a2a;
	}

	:global(.document-preview h3) {
		font-size: 1.1rem;
		font-weight: 600;
		margin-top: 1rem;
		margin-bottom: 0.5rem;
		color: #3a3a3a;
	}

	:global(.document-preview p) {
		margin-bottom: 1rem;
	}

	:global(.document-preview table) {
		width: 100%;
		border-collapse: collapse;
		margin: 1.5rem 0;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		overflow: hidden;
		border-radius: 8px;
	}

	:global(.document-preview thead) {
		background-color: #00548f;
		color: white;
	}

	:global(.document-preview th) {
		padding: 12px;
		text-align: left;
		font-weight: 600;
		font-size: 0.9rem;
	}

	:global(.document-preview td) {
		padding: 12px;
		border-bottom: 1px solid #e0e0e0;
		font-size: 0.9rem;
	}

	:global(.document-preview tbody tr:nth-child(even)) {
		background-color: #f8f9fa;
	}

	:global(.document-preview tbody tr:hover) {
		background-color: #f0f0f0;
	}

	:global(.document-preview ul),
	:global(.document-preview ol) {
		margin-left: 1.5rem;
		margin-bottom: 1rem;
	}

	:global(.document-preview li) {
		margin-bottom: 0.5rem;
	}

	:global(.document-preview strong) {
		font-weight: 600;
		color: #1a1a1a;
	}

	:global(.document-preview em) {
		font-style: italic;
	}
</style>
