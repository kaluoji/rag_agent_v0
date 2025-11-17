# Quick Reference Card

## Startup (2 minutes)

```bash
cd frontend-svelte
npm install
echo 'VITE_API_URL=http://localhost:8000' > .env.local
npm run dev
# Open http://localhost:5173
```

---

## Routes Overview

### Pages (8)

| Route | Purpose |
|-------|---------|
| `/` | Chat interface |
| `/historial` | Query history with search/filter |
| `/consulta/[id]` | Query details with report generation |
| `/novedades` | News and updates feed |

### API Routes (5)

| Endpoint | Purpose |
|----------|---------|
| POST `/api/query` | Process regulatory query |
| POST/GET `/api/report` | Generate and check report status |
| POST/GET `/api/file` | Upload and download files |
| GET/DELETE `/api/history` | Manage query history |

---

## Common Tasks

### Start Development
```bash
npm run dev  # http://localhost:5173
npm run build  # Production build
npm run preview  # Test production
```

### Add New Page
1. Create `src/routes/page/+page.svelte`
2. Optionally create `src/routes/page/+page.server.ts` for SSR
3. Add navigation link in `+layout.svelte`

### Add API Route
1. Create `src/routes/api/endpoint/+server.ts`
2. Implement handler (GET/POST/DELETE)
3. Add validation and error handling

---

## File Structure

```
src/routes/
├── +page.svelte (Chat)
├── +page.server.ts
├── historial/ (History page)
├── consulta/[id]/ (Details page)
├── novedades/ (News page)
└── api/
    ├── query/+server.ts
    ├── report/+server.ts
    ├── file/+server.ts
    └── history/+server.ts
```

---

## Environment Setup

```bash
# .env.local (required)
VITE_API_URL=http://localhost:8000

# Optional timeouts
API_REQUEST_TIMEOUT=30000
API_REPORT_TIMEOUT=120000
API_UPLOAD_TIMEOUT=60000
```

---

## API Usage Example

```svelte
<script>
  import { processQuery } from '$lib/api';

  async function sendQuery(text: string) {
    const result = await processQuery(text, 'banking');
    if (result.error) {
      console.error('Error:', result.error.message);
    } else {
      console.log('Analysis:', result.data);
    }
  }
</script>
```

---

## Store Usage

```svelte
<script>
  import { messageStore, addNotification } from '$lib/stores';

  let messages = [];
  messageStore.subscribe(state => {
    messages = state.messages;
  });

  // Add notification
  addNotification({
    type: 'success',
    message: 'Query processed!',
    duration: 3000
  });
</script>
```

---

## Styling

### Global Styles
Edit `src/app.css` for theme colors and global CSS variables.

### Component Styles
Use `<style>` blocks in `.svelte` files for component-specific styles.

### Dark Mode
- Light: `--color-primary: #005 48f`
- Dark: `[data-theme='dark'] { --color-primary: #93c5fd }`

---

## Accessibility

- All pages WCAG 2.1 AA compliant
- Semantic HTML with ARIA attributes
- Keyboard navigation (Tab, Enter, Escape)
- Focus visible on all interactive elements
- Screen reader support

---

## Testing

### Manual Tests
See **TESTING_CHECKLIST.md** for 150+ test cases

### Key Areas
- Page rendering and layout
- API validation and error handling
- Accessibility compliance
- Mobile responsiveness
- Dark mode functionality
- Performance metrics

---

## Debugging

### Network Issues
1. Check `Network` tab in DevTools
2. Verify `VITE_API_URL` in `.env.local`
3. Ensure backend running on port 8000

### Type Errors
1. Check `$lib/types.ts` imports
2. Verify interface definitions
3. Use TypeScript strict mode

### Styling Issues
1. Check CSS specificity
2. Verify dark mode selectors
3. Test responsive breakpoints

---

## Performance Tips

1. **Lazy load images:** `<img loading="lazy" />`
2. **Code splitting:** Automatic per route
3. **Caching:** Use stores and LocalStorage
4. **Debounce search:** 300ms delay

---

## Color Reference

| Variable | Value | Use |
|----------|-------|-----|
| --color-primary | #005 48f | Links, buttons, accents |
| --color-bg | #ffffff | Page background |
| --color-success | #22c55e | Success states |
| --color-warning | #f59e0b | Warning states |
| --color-error | #dc2626 | Error states |

---

## Responsive Breakpoints

- **Mobile:** < 480px
- **Tablet:** 480px - 768px
- **Desktop:** > 768px

```css
@media (max-width: 768px) {
  /* Mobile and tablet */
}

@media (max-width: 480px) {
  /* Mobile only */
}
```

---

## Support Documents

1. **ROUTES_DOCUMENTATION.md** - Complete API reference (800 lines)
2. **INTEGRATION_GUIDE.md** - Setup and architecture (600 lines)
3. **TESTING_CHECKLIST.md** - Test cases and validation (1,200 lines)
4. **IMPLEMENTATION_COMPLETE.md** - Project summary

---

**Version:** 1.0.0 | **Status:** Production Ready | **Updated:** 2024-11-17
