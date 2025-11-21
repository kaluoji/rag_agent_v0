<script lang="ts">
	import { reportStore } from '$lib/stores';
	import ReportArtifact from '$lib/components/ReportArtifact.svelte';
	import type { Snippet } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { queryStore } from '$lib/stores';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { MessageSquare, History, Newspaper, Plus, Menu, X } from 'lucide-svelte';
	import '../app.css';

	let { children }: { children: Snippet } = $props();

	const currentPath = $derived($page.url.pathname);
	let mobileMenuOpen = $state(false);

	function startNewConversation() {
		queryStore.reset();
		goto('/');
		mobileMenuOpen = false;
	}

	function isActive(path: string): boolean {
		if (path === '/') {
			return currentPath === '/';
		}
		return currentPath.startsWith(path);
	}

	function navigate(path: string) {
		goto(path);
		mobileMenuOpen = false;
	}
</script>

<!-- Contenedor principal -->
<div class="h-screen overflow-x-hidden overflow-y-auto bg-white relative">
	<div class="flex h-full relative">
		<!-- Sidebar Desktop - Absolutamente fijo -->
		<aside class="hidden lg:flex flex-col w-64 bg-white border-r border-slate-200 flex-shrink-0 relative z-10">
			<!-- Header del sidebar -->
			<div class="p-4 border-b">
				<div class="flex items-center gap-3 mb-4">
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

				<Button
					type="button"
					onclick={startNewConversation}
					class="w-full bg-[#00548F] hover:bg-[#003d6b] text-white shadow-sm"
				>
					<Plus class="h-4 w-4 mr-2" />
					Nueva conversación
				</Button>
			</div>

			<!-- Navegación principal -->
			<nav class="flex-1 overflow-auto py-4 px-3">
				<div class="space-y-1">
					<button
						type="button"
						onclick={() => navigate('/')}
						class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors w-full text-left {isActive(
							'/'
						)
							? 'bg-[#00548F]/10 text-[#00548F]'
							: 'hover:bg-slate-100 text-slate-700'}"
					>
						<MessageSquare class="h-4 w-4 flex-shrink-0" />
						<span>Conversaciones</span>
					</button>

					<button
						type="button"
						onclick={() => navigate('/historial')}
						class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors w-full text-left {isActive(
							'/historial'
						)
							? 'bg-[#00548F]/10 text-[#00548F]'
							: 'hover:bg-slate-100 text-slate-700'}"
					>
						<History class="h-4 w-4 flex-shrink-0" />
						<span>Historial</span>
						{#if queryStore.totalQueries > 0}
							<Badge variant="secondary" class="ml-auto h-5 px-1.5 text-xs">
								{queryStore.totalQueries}
							</Badge>
						{/if}
					</button>

					<button
						type="button"
						onclick={() => navigate('/novedades')}
						class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors w-full text-left {isActive(
							'/novedades'
						)
							? 'bg-[#00548F]/10 text-[#00548F]'
							: 'hover:bg-slate-100 text-slate-700'}"
					>
						<Newspaper class="h-4 w-4 flex-shrink-0" />
						<span>Novedades</span>
					</button>
				</div>
			</nav>
		</aside>

		<!-- Mobile Menu Button -->
		<div class="lg:hidden fixed top-4 left-4 z-50">
			<Button
				type="button"
				variant="outline"
				size="icon"
				onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
				class="bg-white shadow-lg"
			>
				{#if mobileMenuOpen}
					<X class="h-5 w-5" />
				{:else}
					<Menu class="h-5 w-5" />
				{/if}
			</Button>
		</div>

		<!-- Mobile Sidebar Overlay -->
		{#if mobileMenuOpen}
			<div
				class="lg:hidden fixed inset-0 bg-black/50 z-40"
				role="button"
				tabindex="0"
				onclick={() => (mobileMenuOpen = false)}
				onkeydown={(e) => e.key === 'Escape' && (mobileMenuOpen = false)}
			></div>

			<aside
				class="lg:hidden fixed left-0 top-0 bottom-0 w-64 bg-white border-r border-slate-200 z-50 flex flex-col"
			>
				<!-- Header del sidebar móvil -->
				<div class="p-4 border-b">
					<div class="flex items-center gap-3 mb-4">
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

					<Button
						type="button"
						onclick={startNewConversation}
						class="w-full bg-[#00548F] hover:bg-[#003d6b] text-white"
					>
						<Plus class="h-4 w-4 mr-2" />
						Nueva conversación
					</Button>
				</div>

				<!-- Navegación móvil -->
				<nav class="flex-1 overflow-auto py-4 px-3">
					<div class="space-y-1">
						<button
							type="button"
							onclick={() => navigate('/')}
							class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors w-full text-left {isActive(
								'/'
							)
								? 'bg-[#00548F]/10 text-[#00548F]'
								: 'hover:bg-slate-100 text-slate-700'}"
						>
							<MessageSquare class="h-4 w-4" />
							<span>Conversaciones</span>
						</button>

						<button
							type="button"
							onclick={() => navigate('/historial')}
							class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors w-full text-left {isActive(
								'/historial'
							)
								? 'bg-[#00548F]/10 text-[#00548F]'
								: 'hover:bg-slate-100 text-slate-700'}"
						>
							<History class="h-4 w-4" />
							<span>Historial</span>
							{#if queryStore.totalQueries > 0}
								<Badge variant="secondary" class="ml-auto h-5 px-1.5 text-xs">
									{queryStore.totalQueries}
								</Badge>
							{/if}
						</button>

						<button
							type="button"
							onclick={() => navigate('/novedades')}
							class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors w-full text-left {isActive(
								'/novedades'
							)
								? 'bg-[#00548F]/10 text-[#00548F]'
								: 'hover:bg-slate-100 text-slate-700'}"
						>
							<Newspaper class="h-4 w-4" />
							<span>Novedades</span>
						</button>
					</div>
				</nav>
			</aside>
		{/if}

		<!-- Main content - Sin ningún ajuste dinámico -->
		<main class="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
			{@render children?.()}
		</main>
	</div>
</div>

<!-- Artifact - Completamente independiente, renderizado fuera del layout principal -->
<ReportArtifact />

<style>
	/* SOLUCIÓN: Forzar scrollbar siempre visible para prevenir layout shift */
	:global(html) {
		overflow-y: scroll; /* ← Scrollbar SIEMPRE visible */
		overflow-x: hidden;
		width: 100%;
		height: 100%;
	}
	
	:global(body) {
		overflow-x: hidden;
		width: 100%;
		margin: 0;
		padding: 0;
	}
</style>