<script lang="ts">
	import { tick } from 'svelte';
	import { Message, MessageAvatar, MessageContent } from '$lib/components/prompt-kit/message';
	import { Loader } from '$lib/components/prompt-kit/loader';
	import {
		PromptInput,
		PromptInputTextarea,
		PromptInputActions
	} from '$lib/components/prompt-kit/prompt-input';
	import {
		FileUpload,
		FileUploadTrigger,
		FileUploadContent
	} from '$lib/components/prompt-kit/file-upload';
	import { Response as AiResponse } from '$lib/components/ai-elements/response';
	import { Alert } from '$lib/components/ui/alert';
	import { Button } from '$lib/components/ui/button';
	import { askQuery, askQueryWithDocuments, fileToDocumentData, startNewConversation, getCurrentSessionId } from '$lib/api/client';
	import { queryStore, reportStore } from '$lib/stores';
	import { onMount } from 'svelte';
	import { AlertCircle, Paperclip, FileText, MessageSquarePlus } from 'lucide-svelte';

	type Role = 'user' | 'assistant';
	type ChatMessage = {
		id: string;
		role: Role;
		content: string;
		reportId?: string;
		reportFilename?: string;
	};

	let messages: ChatMessage[] = $state([]);
	let inputValue = $state('');
	let attachedFiles: File[] = $state([]);
	let chatContainerRef: HTMLElement | null = null;

	onMount(() => {
		queryStore.loadStoredQueries();
	});

	const suggestions: string[] = [
		'Gobierno corporativo CUSF',
		'Reporte financiero CUSF',
		'Gestión de riesgos',
		'Controles PLD CUSF'
	];

	function scrollToBottom() {
		const el = chatContainerRef;
		if (!el) return;

		setTimeout(() => {
			el.scrollTop = el.scrollHeight;
		}, 100);
	}

	function addMessage(role: Role, content: string, reportId?: string, reportFilename?: string) {
		messages = [...messages, { id: crypto.randomUUID(), role, content, reportId, reportFilename }];
		scrollToBottom();
	}

	function handleSuggestionClick(text: string) {
		inputValue = text;
	}

	function handleFilesAdded(files: File[]) {
		attachedFiles = files;
	}

	// ✅ Nueva función para iniciar conversación nueva
	function handleNewConversation() {
		// Limpiar mensajes
		messages = [];
		
		// Limpiar sesión
		startNewConversation();
		
		// Limpiar input
		inputValue = '';
		attachedFiles = [];
		
		// Limpiar stores
		queryStore.reset();
		reportStore.closePreview();
		
		console.log('🔴 Nueva conversación iniciada - Session ID limpiado');
		console.log('🔴 Session ID actual:', getCurrentSessionId());
	}

	async function detectAndShowReport(responseText: string): Promise<{ reportId: string; filename: string } | null> {
		const reportIdMatch = responseText.match(/(\d{8}_\d{6})\.docx/);
		
		if (reportIdMatch) {
			const reportId = reportIdMatch[1];
			const filename = `Reporte_${reportId}.docx`;
			
			console.log('🎯 Reporte detectado con ID:', reportId);
			
			reportStore.setReportId(reportId);
			reportStore.setFilename(filename);
			reportStore.setStatus('ready');
			reportStore.openPreview();
			
			console.log('📂 Artifact abierto, cargando preview...');
			
			try {
				const { getReportHtml } = await import('$lib/api/report');
				const html = await getReportHtml(reportId);
				reportStore.setReportHtml(html);
				console.log('✅ HTML cargado correctamente');
			} catch (error) {
				console.error('❌ Error al cargar HTML del reporte:', error);
			}
			
			return { reportId, filename };
		} else {
			console.log('⚠️ No se detectó patrón de reporte en la respuesta');
			return null;
		}
	}

	async function reopenReport(reportId: string, filename: string) {
		console.log('🔄 Reabriendo reporte:', reportId);
		
		reportStore.setReportId(reportId);
		reportStore.setFilename(filename);
		reportStore.setStatus('ready');
		
		if (!reportStore.reportHtml) {
			try {
				const { getReportHtml } = await import('$lib/api/report');
				const html = await getReportHtml(reportId);
				reportStore.setReportHtml(html);
			} catch (error) {
				console.error('❌ Error al cargar HTML del reporte:', error);
			}
		}
		
		reportStore.openPreview();
	}

	async function handleSubmit() {
		const question = inputValue.trim();
		if (!question && attachedFiles.length === 0) return;

		queryStore.reset();
		addMessage('user', question || '[Consulta con documentos]');
		queryStore.startLoading();
		queryStore.setQuery(question);

		const currentFiles = [...attachedFiles];
		inputValue = '';
		attachedFiles = [];

		try {
			console.log('🔵 Session ID actual antes de enviar:', getCurrentSessionId());
			let responseData;

			if (currentFiles.length > 0) {
				const documents = await Promise.all(currentFiles.map(fileToDocumentData));
				responseData = await askQueryWithDocuments(question, documents);
			} else {
				responseData = await askQuery(question);
			}

			console.log('🟢 Session ID recibido del backend:', responseData.session_id);
			console.log('🟢 Session ID guardado en memoria:', getCurrentSessionId());

			const responseText = responseData.response || JSON.stringify(responseData);
			
			const reportInfo = await detectAndShowReport(responseText);
			
			addMessage('assistant', responseText, reportInfo?.reportId, reportInfo?.filename);

			queryStore.setResponse({
				...responseData,
				type: currentFiles.length > 0 ? 'gap_analysis' : 'consultation',
				hasDocuments: currentFiles.length > 0
			});
			
		} catch (e) {
			const errorMessage = e instanceof Error ? e.message : 'Error desconocido';
			queryStore.setError(errorMessage);
			addMessage('assistant', `Error al procesar la consulta: ${errorMessage}`);
		} finally {
			queryStore.stopLoading();
		}
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSubmit();
		}
	}

</script>


	<section class="flex flex-col h-[100dvh] max-h-[100dvh] bg-white">

	<div class="flex-1 flex flex-col max-w-4xl mx-auto w-full min-h-0">
		<!-- Header con botón de nueva conversación -->
		<header class="px-4 py-4 border-b bg-white flex items-center justify-between">
			<h1 class="text-xl font-semibold text-slate-900">AgentIA</h1>
			
			<!-- ✅ Botón de nueva conversación -->
			{#if messages.length > 0}
				<Button
					type="button"
					variant="outline"
					size="sm"
					onclick={handleNewConversation}
					class="flex items-center gap-2 text-[#00548F] border-[#00548F] hover:bg-[#E6F0FA]"
				>
					<MessageSquarePlus class="h-4 w-4" />
					<span>Nueva conversación</span>
				</Button>
			{/if}
		</header>

		<!-- Chat Container con div scrollable -->
		<div class="flex-1 overflow-hidden min-h-0">
			<div class="h-full overflow-y-auto px-4 py-6 space-y-6" bind:this={chatContainerRef}>
				{#if messages.length === 0}
					<!-- Estado inicial con sugerencias -->
					<div class="flex flex-col items-center justify-center h-full space-y-6">
						<div class="text-center space-y-2 mb-8">
							<h2 class="text-2xl font-semibold text-slate-900">
								¿En qué puedo ayudarte?
							</h2>
						</div>

						<!-- Sugerencias -->
						<div class="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-lg mt-14">
							{#each suggestions as suggestion}
								<button
									type="button"
									onclick={() => handleSuggestionClick(suggestion)}
									class="flex items-center justify-center px-4 py-2 rounded-full bg-[#E6F0FA] text-[#00548F] text-sm font-medium shadow-sm hover:shadow-md border border-[#C9DCEC] hover:bg-[#D9E8F5] transition-all"
								>
									{suggestion}
								</button>
							{/each}
						</div>
					</div>
				{:else}
					<!-- Mensajes del chat -->
					{#each messages as message (message.id)}
						<div
							class="flex gap-4 {message.role === 'user' ? 'justify-end' : 'justify-start'}"
						>
							<Message class="max-w-[85%]">
								{#if message.role === 'assistant'}
									<MessageAvatar
										fallback="AI"
										class="bg-[#00548F] text-white shadow-md"
									/>
								{/if}

								<MessageContent
									markdown={message.role === 'assistant'}
									class="{message.role === 'user'
										? 'bg-slate-900 rounded-2xl'
										: 'bg-slate-50 text-slate-900 rounded-2xl'} px-4 py-3"
								>
									{#if message.role === 'assistant'}
										<AiResponse
											content={message.content}
											class="text-sm prose prose-slate"
										/>
										
										<!-- Botón para reabrir el reporte -->
										{#if message.reportId && message.reportFilename}
											<div class="mt-4 pt-3 border-t border-slate-200">
												<Button
													type="button"
													variant="outline"
													size="sm"
													onclick={() => reopenReport(message.reportId!, message.reportFilename!)}
													class="flex items-center gap-2 text-[#00548F] border-[#00548F] hover:bg-[#E6F0FA]"
												>
													<FileText class="h-4 w-4" />
													<span>Ver reporte</span>
												</Button>
											</div>
										{/if}
									{:else}
										<p class="text-sm whitespace-pre-wrap user-message-text">
											{message.content}
										</p>
									{/if}
								</MessageContent>
							</Message>
						</div>
					{/each}

					{#if queryStore.isLoading}
						<div class="flex gap-4">
							<Message class="max-w-[85%]">
								<MessageAvatar fallback="AI" class="bg-[#00548F] text-white" />
								<MessageContent class="bg-slate-50 rounded-2xl px-4 py-3">
									<Loader variant="dots" size="sm" text="Pensando..." />
								</MessageContent>
							</Message>
						</div>
					{/if}
				{/if}
			</div>
		</div>

		<!-- Error Alert -->
		{#if queryStore.error}
			<div class="px-4 pb-2">
				<Alert variant="destructive" class="flex items-start gap-2">
					<AlertCircle class="h-4 w-4 mt-0.5" />
					<div>
						<p class="font-semibold">Error al procesar la consulta</p>
						<p class="text-sm">{queryStore.error}</p>
					</div>
				</Alert>
			</div>
		{/if}

		<!-- Input Area -->
		<div class="px-4 pb-4 bg-white border-t">
			<div class="max-w-3xl mx-auto space-y-3 py-3">
				<!-- File Upload indicador -->
				{#if attachedFiles.length > 0}
					<div
						class="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 px-3 py-2 rounded-lg"
					>
						<Paperclip class="h-3 w-3" />
						<span>{attachedFiles.length} archivo(s) adjunto(s)</span>
						<button
							type="button"
							onclick={() => (attachedFiles = [])}
							class="ml-auto text-red-600 hover:text-red-700 font-medium"
						>
							Eliminar
						</button>
					</div>
				{/if}

				<!-- Prompt Input -->
				<PromptInput
					isLoading={queryStore.isLoading}
					value={inputValue}
					onValueChange={(v) => (inputValue = v)}
					onSubmit={handleSubmit}
					maxHeight={150}
					class="border-2 border-slate-200 rounded-2xl shadow-sm focus-within:border-[#00548F] transition-colors"
				>
					<PromptInputTextarea
						placeholder="Escribe tu consulta normativa..."
						disabled={queryStore.isLoading}
						onkeydown={handleKeyDown}
						class="resize-none px-4 py-3 text-sm"
					/>

					<PromptInputActions class="px-2 pb-2">
						<FileUpload onFilesAdded={handleFilesAdded} multiple accept=".pdf,.doc,.docx">
							<FileUploadTrigger class="h-8 w-8 p-0">
								<Paperclip class="h-4 w-4" />
							</FileUploadTrigger>
						</FileUpload>

						<Button
							type="button"
							onclick={handleSubmit}
							disabled={queryStore.isLoading ||
								(!inputValue.trim() && attachedFiles.length === 0)}
							size="sm"
							class="bg-[#00548F] hover:bg-[#003d6b] text-white rounded-xl"
						>
							{#if queryStore.isLoading}
								⏳
							{:else}
								Enviar
							{/if}
						</Button>
					</PromptInputActions>
				</PromptInput>

				<p class="text-xs text-center text-slate-500">
					AgentIA puede cometer errores. Verifica la información importante.
				</p>
			</div>
		</div>
	</div>
</section>


<style>
	/* Forzar color blanco en mensajes del usuario */
	:global(.user-message-text) {
		color: white !important;
	}
</style>