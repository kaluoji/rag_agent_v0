<script lang="ts">
	import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar/index.js";
	import { cn } from "$lib/utils";

	let {
		src,
		alt,
		fallback,
		class: className,
	}: {
		src: string;
		alt: string;
		fallback?: string;
		class?: string;
	} = $props();
</script>

<Avatar class="h-8 w-8 shrink-0">
	<AvatarImage {src} {alt} />
	{#if fallback}
		<AvatarFallback class={className}>
			{fallback}
		</AvatarFallback>
	{/if}
</Avatar>
