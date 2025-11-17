<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { uiStore, toggleTheme, setSidebarOpen } from '$lib/stores';
  import { initWebSocket, destroyWebSocket } from '$lib/websocket';
  import '../app.css';

  /**
   * Main application layout with header, sidebar, and theme support
   * Handles global initialization and theme management
   */

  let isMounted = false;
  let theme: 'light' | 'dark' = 'light';
  let sidebarOpen: boolean = true;

  // Subscribe to UI store for theme and sidebar changes
  const unsubscribeUI = uiStore.subscribe((state) => {
    theme = state.theme;
    sidebarOpen = state.sidebarOpen;

    // Update data attribute for CSS theme variable
    if (isMounted) {
      document.documentElement.setAttribute('data-theme', theme);
    }
  });

  onMount(async () => {
    isMounted = true;

    // Set initial theme
    document.documentElement.setAttribute('data-theme', theme);

    // Initialize WebSocket connection for real-time updates
    try {
      await initWebSocket();
      console.log('[App] WebSocket initialized');
    } catch (error) {
      console.warn('[App] WebSocket initialization failed:', error);
      // WebSocket is optional - app continues to work without it
    }
  });

  onDestroy(() => {
    unsubscribeUI();
    destroyWebSocket();
  });

  /**
   * Toggle theme handler
   */
  function handleThemeToggle() {
    toggleTheme();
  }

  /**
   * Toggle sidebar handler
   */
  function handleSidebarToggle() {
    setSidebarOpen(!sidebarOpen);
  }
</script>

<div class="app-wrapper" data-theme={theme}>
  <!-- Header -->
  <header class="app-header">
    <div class="header-content">
      <!-- Logo and title -->
      <div class="header-brand">
        <button
          class="sidebar-toggle"
          on:click={handleSidebarToggle}
          aria-label="Toggle sidebar"
          title="Toggle sidebar"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>

        <div class="logo">
          <svg
            width="32"
            height="32"
            viewBox="0 0 32 32"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
          >
            <!-- Placeholder logo - replace with actual SVG -->
            <rect width="32" height="32" rx="4" fill="var(--color-primary)" />
            <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="18" font-weight="bold">
              RAG
            </text>
          </svg>
          <h1>RAG Regulatory</h1>
        </div>
      </div>

      <!-- Header actions -->
      <div class="header-actions">
        <button
          class="theme-toggle"
          on:click={handleThemeToggle}
          aria-label="Toggle theme"
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {#if theme === 'light'}
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
              ></path>
            </svg>
          {:else}
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
          {/if}
        </button>

        <!-- User menu placeholder -->
        <button class="user-menu" aria-label="User menu">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </button>
      </div>
    </div>
  </header>

  <div class="app-container">
    <!-- Sidebar -->
    <aside class="app-sidebar" class:open={sidebarOpen}>
      <nav class="sidebar-nav">
        <ul>
          <li>
            <a href="/" class:active={$page.url.pathname === '/'}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
              <span>Inicio</span>
            </a>
          </li>
          <li>
            <a href="/consultas" class:active={$page.url.pathname === '/consultas'}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
              <span>Consultas</span>
            </a>
          </li>
          <li>
            <a href="/reportes" class:active={$page.url.pathname === '/reportes'}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="12" y1="19" x2="12" y2="5"></line>
                <line x1="9" y1="12" x2="15" y2="12"></line>
              </svg>
              <span>Reportes</span>
            </a>
          </li>
          <li>
            <a href="/historial" class:active={$page.url.pathname === '/historial'}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              <span>Historial</span>
            </a>
          </li>
        </ul>
      </nav>

      <div class="sidebar-footer">
        <button class="settings-btn" aria-label="Settings">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"></circle>
            <path
              d="M12 1v6m0 6v6M4.22 4.22l4.24 4.24m5.08 5.08l4.24 4.24M1 12h6m6 0h6M4.22 19.78l4.24-4.24m5.08-5.08l4.24-4.24"
            ></path>
          </svg>
          <span>Configuración</span>
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <main class="app-main">
      <slot />
    </main>
  </div>
</div>

<style>
  :global(html) {
    scroll-behavior: smooth;
  }

  :global(body) {
    margin: 0;
    padding: 0;
  }

  :global(#app) {
    width: 100%;
    height: 100vh;
  }

  .app-wrapper {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background-color: var(--color-bg);
    color: var(--color-text-primary);
    transition: background-color var(--transition-base), color var(--transition-base);
  }

  /* Header */
  .app-header {
    display: flex;
    align-items: center;
    height: 64px;
    background-color: var(--color-bg-elevated);
    border-bottom: 1px solid var(--color-border);
    box-shadow: var(--shadow-sm);
    position: sticky;
    top: 0;
    z-index: 100;
    padding: 0 1rem;
  }

  .header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    max-width: 1600px;
    margin: 0 auto;
  }

  .header-brand {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex: 1;
  }

  .sidebar-toggle {
    display: none;
    width: 40px;
    height: 40px;
    border: none;
    background: none;
    color: var(--color-text-primary);
    cursor: pointer;
    border-radius: 6px;
    transition: background-color var(--transition-fast);
  }

  .sidebar-toggle:hover {
    background-color: var(--color-bg-alt);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: var(--color-primary);
    text-decoration: none;
    font-weight: 700;
    font-size: 1.25rem;
  }

  .logo h1 {
    margin: 0;
    font-size: 1.25rem;
  }

  .logo svg {
    border-radius: 4px;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .theme-toggle,
  .user-menu {
    width: 40px;
    height: 40px;
    border: none;
    background: none;
    color: var(--color-text-primary);
    cursor: pointer;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color var(--transition-fast);
  }

  .theme-toggle:hover,
  .user-menu:hover {
    background-color: var(--color-bg-alt);
  }

  .theme-toggle:active,
  .user-menu:active {
    background-color: var(--color-border);
  }

  /* Container */
  .app-container {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  /* Sidebar */
  .app-sidebar {
    width: 280px;
    background-color: var(--color-bg-elevated);
    border-right: 1px solid var(--color-border);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    transition: transform var(--transition-base), width var(--transition-base);
    z-index: 50;
  }

  .sidebar-nav {
    flex: 1;
    padding: 1rem 0;
  }

  .sidebar-nav ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .sidebar-nav li {
    margin: 0;
  }

  .sidebar-nav a {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    color: var(--color-text-secondary);
    text-decoration: none;
    font-weight: 500;
    transition: all var(--transition-fast);
  }

  .sidebar-nav a:hover {
    color: var(--color-primary);
    background-color: var(--color-bg-alt);
  }

  .sidebar-nav a.active {
    color: var(--color-primary);
    background-color: rgba(0, 84, 143, 0.1);
    border-left: 3px solid var(--color-primary);
    padding-left: calc(1rem - 3px);
  }

  .sidebar-footer {
    padding: 1rem;
    border-top: 1px solid var(--color-border);
  }

  .settings-btn {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background-color: transparent;
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all var(--transition-fast);
  }

  .settings-btn:hover {
    color: var(--color-primary);
    background-color: var(--color-bg-alt);
    border-color: var(--color-primary);
  }

  /* Main content */
  .app-main {
    flex: 1;
    overflow-y: auto;
    padding: 2rem;
    background-color: var(--color-bg);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .header-brand {
      gap: 0.5rem;
    }

    .logo {
      font-size: 1.125rem;
    }

    .logo h1 {
      font-size: 1.125rem;
    }

    .sidebar-toggle {
      display: flex;
    }

    .app-sidebar {
      position: absolute;
      left: 0;
      top: 64px;
      height: calc(100vh - 64px);
      transform: translateX(-100%);
    }

    .app-sidebar.open {
      transform: translateX(0);
      box-shadow: var(--shadow-lg);
    }

    .app-main {
      padding: 1rem;
    }
  }

  @media (max-width: 480px) {
    .app-header {
      padding: 0 0.75rem;
      height: 56px;
    }

    .logo h1 {
      display: none;
    }

    .app-sidebar {
      width: 240px;
    }

    .app-main {
      padding: 0.75rem;
    }
  }
</style>
