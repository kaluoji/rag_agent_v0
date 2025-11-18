<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { goto } from '$app/navigation';
	import { Newspaper, ArrowLeft } from 'lucide-svelte';
</script>

<div class="container mx-auto p-6 max-w-2xl">
	<Card class="p-12 text-center">
		<Newspaper class="h-24 w-24 text-slate-300 mx-auto mb-6" />

		<h1 class="text-3xl font-bold text-slate-900 mb-4">Novedades Normativas</h1>

		<p class="text-lg text-slate-600 mb-6">
			Esta sección está en construcción. Pronto podrás acceder a las últimas actualizaciones y
			cambios normativos relevantes para tu sector.
		</p>

		<div class="space-y-3 text-left max-w-md mx-auto mb-8">
			<div class="flex items-start gap-3">
				<div class="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
				<p class="text-slate-600">Actualizaciones normativas en tiempo real</p>
			</div>
			<div class="flex items-start gap-3">
				<div class="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
				<p class="text-slate-600">Resúmenes ejecutivos de cambios regulatorios</p>
			</div>
			<div class="flex items-start gap-3">
				<div class="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
				<p class="text-slate-600">Alertas personalizadas por sector</p>
			</div>
		</div>

		<Button onclick={() => goto('/')}>
			<ArrowLeft class="h-4 w-4 mr-2" />
			Volver al inicio
		</Button>
	</Card>
</div>
