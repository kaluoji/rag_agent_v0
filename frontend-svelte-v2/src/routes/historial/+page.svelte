<script lang="ts">
	import { queryStore } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Card } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '$lib/components/ui/dialog';
	import { Separator } from '$lib/components/ui/separator';
	import { Search, Trash2, Share2, Eye, Calendar, FileText } from 'lucide-svelte';

	// Estado local con runes
	let searchTerm = $state('');
	let selectedFilter = $state<'all' | 'consultation' | 'gap_analysis'>('all');
	let showClearDialog = $state(false);

	// Computed: consultas filtradas
	let filteredQueries = $derived.by(() => {
		let queries = queryStore.recentQueries;

		// Filtrar por tipo
		if (selectedFilter !== 'all') {
			queries = queries.filter((q) => q.type === selectedFilter);
		}

		// Filtrar por búsqueda
		if (searchTerm.trim()) {
			queries = queryStore.searchInHistory(searchTerm);
		}

		// Limitar a 50 consultas
		return queries.slice(0, 50);
	});

	// Formatear fecha relativa
	function formatRelativeTime(timestamp: string): string {
		const now = new Date();
		const date = new Date(timestamp);
		const diff = now.getTime() - date.getTime();

		const seconds = Math.floor(diff / 1000);
		const minutes = Math.floor(seconds / 60);
		const hours = Math.floor(minutes / 60);
		const days = Math.floor(hours / 24);

		if (seconds < 60) return 'Hace un momento';
		if (minutes < 60) return `Hace ${minutes} min`;
		if (hours < 24) return `Hace ${hours} h`;
		if (days === 1) return 'Ayer';
		if (days < 7) return `Hace ${days} días`;

		return date.toLocaleDateString('es-ES', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
	}

	// Truncar texto de forma segura
	function truncate(text: string | null | undefined, maxLength: number): string {
		if (!text || typeof text !== 'string') return '';
		if (text.length <= maxLength) return text;
		return text.slice(0, maxLength) + '...';
	}

	// Acciones
	function viewQuery(id: string) {
		goto(`/consulta/${id}`);
	}

	function shareQuery(id: string) {
		const url = `${window.location.origin}/consulta/${id}`;
		navigator.clipboard.writeText(url);
		alert('URL copiada al portapapeles');
	}

	function deleteQuery(id: string) {
		if (confirm('¿Eliminar esta consulta del historial?')) {
			queryStore.removeQueryFromHistory(id);
		}
	}

	function clearAllHistory() {
		queryStore.clearAllHistory();
		showClearDialog = false;
	}

	// Obtener badge para tipo
	function getTypeBadge(type: string) {
		if (type === 'gap_analysis') {
			return { label: 'Análisis GAP', variant: 'default' as const };
		}
		return { label: 'Consulta', variant: 'secondary' as const };
	}
</script>

<div class="container mx-auto p-6 max-w-7xl">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-slate-900 mb-2">Historial de Consultas</h1>
		<p class="text-slate-600">
			Revisa y gestiona tus consultas anteriores ({queryStore.totalQueries} total)
		</p>
	</div>

	<!-- Barra de búsqueda y filtros -->
	<div class="mb-6 flex flex-col sm:flex-row gap-4">
		<!-- Búsqueda -->
		<div class="relative flex-1">
			<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
			<Input
				type="text"
				placeholder="Buscar en historial..."
				class="pl-10"
				bind:value={searchTerm}
			/>
		</div>

		<!-- Filtros -->
		<div class="flex gap-2">
			<Button
				type="button"
				variant={selectedFilter === 'all' ? 'default' : 'outline'}
				onclick={() => (selectedFilter = 'all')}
			>
				Todas
			</Button>
			<Button
				type="button"
				variant={selectedFilter === 'gap_analysis' ? 'default' : 'outline'}
				onclick={() => (selectedFilter = 'gap_analysis')}
			>
				Análisis GAP
			</Button>
			<Button
				type="button"
				variant={selectedFilter === 'consultation' ? 'default' : 'outline'}
				onclick={() => (selectedFilter = 'consultation')}
			>
				Consultas
			</Button>
		</div>

		<!-- Limpiar todo -->
		{#if queryStore.totalQueries > 0}
			<Button 
				type="button"
				variant="destructive" 
				onclick={() => (showClearDialog = true)}
			>
				<Trash2 class="h-4 w-4 mr-2" />
				Limpiar Todo
			</Button>
		{/if}
	</div>

	<Separator class="mb-6" />

	<!-- Grid de consultas -->
	{#if filteredQueries.length === 0}
		<div class="text-center py-16">
			<FileText class="h-16 w-16 text-slate-300 mx-auto mb-4" />
			<h3 class="text-xl font-semibold text-slate-700 mb-2">No hay consultas</h3>
			<p class="text-slate-500">
				{searchTerm ? 'No se encontraron resultados para tu búsqueda' : 'Aún no has realizado ninguna consulta'}
			</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each filteredQueries as query (query.id)}
				<Card class="p-5 hover:shadow-xl transition-all cursor-pointer group border-2 hover:border-[#00548F]">
					<!-- Header de la card -->
					<div class="flex items-start justify-between mb-3">
						<Badge 
							variant={getTypeBadge(query.type).variant}
							class="bg-slate-900 text-white"
						>
							{getTypeBadge(query.type).label}
						</Badge>
						<div class="flex items-center gap-1 text-xs text-slate-500">
							<Calendar class="h-3 w-3" />
							{formatRelativeTime(query.timestamp)}
						</div>
					</div>

					<!-- Contenido -->
					<div 
						class="mb-4" 
						role="button"
						tabindex="0"
						onclick={() => viewQuery(query.id)}
						onkeydown={(e) => e.key === 'Enter' && viewQuery(query.id)}
					>
						<h3 class="font-semibold text-slate-900 mb-2 line-clamp-2">
							{query.text}
						</h3>
						<p class="text-sm text-slate-600 line-clamp-3">
							{truncate(query.response, 150)}
						</p>
					</div>

					<Separator class="mb-3" />

					<!-- Acciones -->
					<div class="flex gap-2">
						<Button 
							type="button"
							size="sm" 
							variant="outline" 
							onclick={() => viewQuery(query.id)}
						>
							<Eye class="h-4 w-4 mr-1" />
							Ver
						</Button>
						<Button
							type="button"
							size="sm"
							variant="ghost"
							onclick={() => shareQuery(query.id)}
						>
							<Share2 class="h-4 w-4" />
						</Button>
						<Button
							type="button"
							size="sm"
							variant="ghost"
							onclick={() => deleteQuery(query.id)}
							class="text-red-600 hover:text-red-700 hover:bg-red-50"
						>
							<Trash2 class="h-4 w-4" />
						</Button>
					</div>
				</Card>
			{/each}
		</div>
	{/if}
</div>

<!-- Dialog de confirmación para limpiar todo -->
<Dialog bind:open={showClearDialog}>
	<DialogContent>
		<DialogHeader>
			<DialogTitle>¿Limpiar todo el historial?</DialogTitle>
			<DialogDescription>
				Esta acción eliminará permanentemente todas las {queryStore.totalQueries} consultas guardadas.
				No se puede deshacer.
			</DialogDescription>
		</DialogHeader>
		<DialogFooter>
			<Button 
				type="button"
				variant="outline" 
				onclick={() => (showClearDialog = false)}
			>
				Cancelar
			</Button>
			<Button 
				type="button"
				variant="destructive" 
				onclick={clearAllHistory}
			>
				Sí, eliminar todo
			</Button>
		</DialogFooter>
	</DialogContent>
</Dialog>

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.line-clamp-3 {
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>