<script lang="ts">
	import type { Snippet } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { queryStore } from '$lib/stores';
	import { Badge } from '$lib/components/ui/badge';
	import { Separator } from '$lib/components/ui/separator';
	import * as Sidebar from '$lib/components/ui/sidebar';
	import { Button } from '$lib/components/ui/button';
	import { MessageSquare, History, Newspaper, Plus, Menu } from 'lucide-svelte';
	import '../app.css';

	// Declarar children como prop de tipo Snippet (requerido en Svelte 5 para layouts)
	let { children }: { children: Snippet } = $props();

	// Detectar ruta actual
	const currentPath = $derived($page.url.pathname);

	function startNewConversation() {
		goto('/');
	}

	// Helper para verificar si ruta está activa
	function isActive(path: string): boolean {
		if (path === '/') {
			return currentPath === '/';
		}
		return currentPath.startsWith(path);
	}
</script>

<Sidebar.Provider>
	<Sidebar.Root>
		<!-- Header del sidebar -->
		<Sidebar.Header class="border-b">
			<div class="flex items-center gap-3 p-4">
				<div
					class="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#00548F] text-white font-semibold shadow-sm"
				>
					AI
				</div>
				<div>
					<div class="text-sm font-semibold text-slate-900">AgentIA</div>
					<div class="text-xs text-slate-500">Compliance Assistant</div>
				</div>
			</div>

			<!-- Botón nueva conversación -->
			<div class="px-3 pb-3">
				<button
					type="button"
					class="w-full flex items-center justify-center gap-2 rounded-xl border border-[#00548F33] bg-[#00548F14] px-3 py-2.5 text-sm font-semibold text-[#00548F] hover:bg-[#00548F20] transition-colors"
					onclick={startNewConversation}
				>
					<Plus class="h-4 w-4" />
					Nueva conversación
				</button>
			</div>
		</Sidebar.Header>

		<!-- Navegación principal -->
		<Sidebar.Content>
			<Sidebar.Group>
				<Sidebar.GroupContent class="space-y-1">
					<!-- Conversaciones -->
					<a
						href="/"
						class="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-slate-100 transition-colors text-sm"
						class:active={isActive('/')}
					>
						<MessageSquare class="h-4 w-4" />
						<span class="flex-1">Conversaciones</span>
					</a>

					<!-- Historial -->
					<a
						href="/historial"
						class="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-slate-100 transition-colors text-sm"
						class:active={isActive('/historial')}
					>
						<History class="h-4 w-4" />
						<span class="flex-1">Historial</span>
						{#if queryStore.totalQueries > 0}
							<Badge variant="secondary" class="h-5 px-1.5 text-xs">
								{queryStore.totalQueries}
							</Badge>
						{/if}
					</a>

					<!-- Novedades -->
					<a
						href="/novedades"
						class="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-slate-100 transition-colors text-sm"
						class:active={isActive('/novedades')}
					>
						<Newspaper class="h-4 w-4" />
						<span class="flex-1">Novedades</span>
					</a>
				</Sidebar.GroupContent>
			</Sidebar.Group>
		</Sidebar.Content>

		<!-- Footer disclaimer -->
		<Sidebar.Footer class="border-t">
			<div class="px-4 py-3 text-xs text-slate-500 leading-relaxed">
				AgentIA puede cometer errores. Verifica la información importante.
			</div>
		</Sidebar.Footer>
	</Sidebar.Root>

	<!-- Main content -->
	<main class="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-50">
		<!-- Trigger para móvil -->
		<div class="lg:hidden p-2 border-b bg-white">
			<Sidebar.Trigger asChild>
				<Button variant="ghost" size="icon">
					<Menu class="h-5 w-5" />
				</Button>
			</Sidebar.Trigger>
		</div>

		{@render children?.()}
	</main>
</Sidebar.Provider>

<style>
	a.active {
		background-color: rgba(0, 84, 143, 0.08);
		color: #00548f;
		font-weight: 600;
	}

	a.active :global(svg) {
		color: #00548f;
	}
</style>
  