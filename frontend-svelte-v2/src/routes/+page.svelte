<script lang="ts">
	import {
		ChatContainerRoot,
		ChatContainerContent,
		ChatContainerScrollAnchor
	} from '$lib/components/prompt-kit/chat-container';

	import { Message, MessageAvatar, MessageContent } from '$lib/components/prompt-kit/message';

	import { Loader } from '$lib/components/prompt-kit/loader';

	import {
		PromptInput,
		PromptInputTextarea,
		PromptInputActions,
		PromptInputAction
	} from '$lib/components/prompt-kit/prompt-input';

	import { PromptSuggestion } from '$lib/components/prompt-kit/prompt-suggestion';

	import {
		FileUpload,
		FileUploadTrigger,
		FileUploadContent
	} from '$lib/components/prompt-kit/file-upload';

	import { Response as AiResponse } from '$lib/components/ai-elements/response';
	import { Alert } from '$lib/components/ui/alert';
	import type { DocumentData } from '$lib/types/backend';
	import { submitQuery, submitQueryWithDocuments, filesToDocumentData } from '$lib/api';
	import { queryStore } from '$lib/stores';
	import { onMount } from 'svelte';
	import { AlertCircle } from 'lucide-svelte';

	type Role = 'user' | 'assistant';

	type ChatMessage = {
		id: string;
		role: Role;
		content: string;
	};

	let messages: ChatMessage[] = $state([]);
	let inputValue = $state('');
	let attachedFiles: File[] = $state([]);

	// Cargar historial al montar
	onMount(() => {
		queryStore.loadStoredQueries();
	});
  
	const suggestions: string[] = [
		'Explica brevemente los requisitos clave de la Circular X para seguros de autos.',
		'Realiza un análisis GAP entre mi política interna y la normativa de blanqueo de capitales.',
		'Resume las principales obligaciones de reporting para la DGSFP en materia de solvencia.',
		'¿Qué cambios normativos relevantes ha habido en Solvencia II en los últimos 12 meses?'
	];

	function addMessage(role: Role, content: string) {
		messages = [...messages, { id: crypto.randomUUID(), role, content }];
	}

	function handleSuggestionClick(text: string) {
		inputValue = text;
	}

	function handleFilesAdded(files: File[]) {
		attachedFiles = files;
	}

	async function handleSubmit() {
		const question = inputValue.trim();

		if (!question && attachedFiles.length === 0) return;

		// Limpiar error previo
		queryStore.reset();

		// Agregar mensaje del usuario al chat
		addMessage('user', question || '[Consulta con documentos]');

		// Iniciar loading
		queryStore.startLoading();
		queryStore.setQuery(question);

		try {
			let responseData;

			// Enviar con o sin documentos
			if (attachedFiles.length > 0) {
				const documents = await filesToDocumentData(attachedFiles);
				responseData = await submitQueryWithDocuments(question, documents);
			} else {
				responseData = await submitQuery(question);
			}

			// Extraer texto de respuesta
			const responseText = responseData.response || JSON.stringify(responseData);

			// Agregar respuesta al chat
			addMessage('assistant', responseText);

			// Guardar en el store (automáticamente guarda en historial)
			queryStore.setResponse({
				...responseData,
				type: attachedFiles.length > 0 ? 'gap_analysis' : 'consultation',
				hasDocuments: attachedFiles.length > 0
			});

			// Limpiar inputs
			inputValue = '';
			attachedFiles = [];
		} catch (e) {
			const errorMessage = e instanceof Error ? e.message : 'Error desconocido';
			queryStore.setError(errorMessage);
			addMessage('assistant', `Error al procesar la consulta: ${errorMessage}`);
		} finally {
			queryStore.stopLoading();
		}
	}
  </script>
  
  <section class="flex flex-col h-[100dvh] max-h-[100dvh] bg-background">
    <div class="flex-1 flex flex-col max-w-5xl mx-auto w-full px-4 py-6 gap-4">
      <!-- Header -->
      <header class="space-y-1">
        <h1 class="text-2xl font-semibold tracking-tight">
          Asistente Normativo
        </h1>
        <p class="text-sm text-muted-foreground">
          Lanza consultas normativas o sube documentación para análisis GAP.
        </p>
      </header>
  
      <!-- Chat -->
      <ChatContainerRoot
        class="flex-1 border rounded-xl bg-card overflow-hidden flex flex-col"
      >
        <ChatContainerContent class="flex-1 px-4 py-3 space-y-4 overflow-y-auto">
          {#if messages.length === 0}
            <div class="text-sm text-muted-foreground text-center mt-8">
              Empieza escribiendo una consulta o selecciona una sugerencia.
            </div>
          {/if}
  
          {#each messages as message (message.id)}
            <div class={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <Message class="max-w-[80%]">
                {#if message.role === 'assistant'}
                  <MessageAvatar fallback="AI" />
                {/if}
  
                <MessageContent markdown={message.role === 'assistant'}>
                  {#if message.role === 'assistant'}
                    <AiResponse content={message.content} class="text-sm" />
                  {:else}
                    {message.content}
                  {/if}
                </MessageContent>
              </Message>
            </div>
          {/each}
  
					{#if queryStore.isLoading}
						<Message class="max-w-[60%]">
							<MessageAvatar fallback="AI" />
							<MessageContent>
								<Loader variant="dots" size="sm" text="Pensando..." />
							</MessageContent>
						</Message>
					{/if}
				</ChatContainerContent>

				<ChatContainerScrollAnchor />
			</ChatContainerRoot>

			{#if queryStore.error}
				<Alert variant="destructive" class="flex items-start gap-2">
					<AlertCircle class="h-4 w-4 mt-0.5" />
					<div>
						<p class="font-semibold">Error al procesar la consulta</p>
						<p class="text-sm">{queryStore.error}</p>
					</div>
				</Alert>
			{/if}
  
			<!-- Sugerencias - Centradas y más cortas -->
			<div class="flex flex-wrap justify-center gap-2 max-w-3xl mx-auto">
				{#each suggestions as suggestion}
					<button
						type="button"
						onclick={() => handleSuggestionClick(suggestion)}
						class="px-3 py-1.5 text-xs rounded-full border border-slate-200 bg-white hover:bg-slate-50 transition-colors max-w-xs text-center"
					>
						{suggestion.slice(0, 60)}...
					</button>
				{/each}
			</div>
  
			<!-- File Upload -->
			<FileUpload onFilesAdded={handleFilesAdded} multiple accept=".pdf,.doc,.docx">
				<FileUploadContent
					class="flex items-center justify-between text-xs text-muted-foreground border rounded-lg px-3 py-2 cursor-pointer bg-white mb-3"
				>
					<span>
						{#if attachedFiles.length === 0}
							📎 Arrastra documentos o haz clic (PDF, DOC, DOCX)
						{:else}
							✅ {attachedFiles.length} archivo(s) adjunto(s)
						{/if}
					</span>

					<FileUploadTrigger class="text-xs font-medium underline">
						Seleccionar
					</FileUploadTrigger>
				</FileUploadContent>
			</FileUpload>

			<!-- Prompt Input - SIN container externo -->
			<PromptInput
				isLoading={queryStore.isLoading}
				value={inputValue}
				onValueChange={(v) => (inputValue = v)}
				onSubmit={handleSubmit}
				maxHeight={200}
			>
				<PromptInputTextarea
					placeholder="Escribe tu consulta normativa..."
					disabled={queryStore.isLoading}
				/>

				<PromptInputActions>
					<PromptInputAction>
						<button
							type="button"
							onclick={handleSubmit}
							class="px-4 py-2 rounded-md bg-[#00548F] hover:bg-[#003d6b] text-white text-sm font-medium disabled:opacity-60 transition-colors"
							disabled={queryStore.isLoading || !inputValue.trim()}
						>
							{#if queryStore.isLoading}
								⏳ Enviando...
							{:else}
								Enviar ➤
							{/if}
						</button>
					</PromptInputAction>
				</PromptInputActions>
			</PromptInput>
	</div>
</section>
  