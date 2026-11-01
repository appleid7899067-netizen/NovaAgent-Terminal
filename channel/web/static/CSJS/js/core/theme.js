/* Light/dark theme toggle.
   Split out of console.js. These are classic scripts sharing one global
   scope; see channel/web/README.md before changing the load order. */

// =====================================================================
// Theme
// =====================================================================
const THEME_OPTIONS = [
    { id: 'dark', name: 'Dark', swatch: '#7b61ff', note: 'Focused' },
    { id: 'light', name: 'Light', swatch: '#f8fafc', note: 'Clear' },
    { id: 'aurora', name: 'Aurora', swatch: '#62f5c7', note: 'Living' },
    { id: 'midnight', name: 'Midnight', swatch: '#b79cff', note: 'Deep' },
    { id: 'forest', name: 'Forest', swatch: '#6ee7b7', note: 'Grounded' },
    { id: 'ocean', name: 'Ocean', swatch: '#38bdf8', note: 'Open' },
    { id: 'rose', name: 'Rose', swatch: '#f472b6', note: 'Warm' },
    { id: 'amber', name: 'Amber', swatch: '#fbbf24', note: 'Bright' },
    { id: 'cyber', name: 'Cyber', swatch: '#00f5d4', note: 'Electric' },
    { id: 'mono', name: 'Mono', swatch: '#ffffff', note: 'Quiet' },
];
let currentTheme = THEME_OPTIONS.some(x => x.id === localStorage.getItem('cow_theme'))
    ? localStorage.getItem('cow_theme') : 'dark';

function applyTheme() {
    const root = document.documentElement;
    root.classList.remove(...THEME_OPTIONS.filter(x => x.id !== 'dark' && x.id !== 'light').map(x => 'theme-' + x.id));
    root.classList.toggle('dark', currentTheme === 'dark' || currentTheme !== 'light');
    if (currentTheme !== 'dark' && currentTheme !== 'light') root.classList.add('theme-' + currentTheme);
    const icon = document.getElementById('theme-icon');
    if (icon) icon.className = currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    const light = document.getElementById('hljs-light');
    const dark = document.getElementById('hljs-dark');
    if (light) light.disabled = currentTheme !== 'light';
    if (dark) dark.disabled = currentTheme === 'light';
    renderThemeOptions();
    rerenderMermaidDiagrams();
}

function setTheme(themeId) {
    if (!THEME_OPTIONS.some(x => x.id === themeId)) return;
    currentTheme = themeId;
    try { localStorage.setItem('cow_theme', currentTheme); } catch (_) { /* private mode */ }
    applyTheme();
}

function renderThemeOptions() {
    const host = document.getElementById('theme-options');
    if (!host) return;
    host.innerHTML = THEME_OPTIONS.map(theme => `
        <button type="button" class="cow-theme-option theme-card" role="radio"
                aria-checked="${theme.id === currentTheme}" aria-current="${theme.id === currentTheme}"
                onclick="setTheme('${theme.id}')">
            <span class="cow-theme-swatch" style="--swatch:${theme.swatch}"></span>
            <span><strong>${escapeHtml(t('theme_' + theme.id) || theme.name)}</strong>
            <small>${escapeHtml(theme.note)}</small></span>
        </button>`).join('');
}

function renderThemeView() { renderThemeOptions(); }

function toggleTheme() {
    setTheme(currentTheme === 'light' ? 'dark' : 'light');
}

// Mermaid bakes the theme colors into the rendered SVG, so a theme switch
// re-renders diagrams the user already previewed. Never-previewed blocks are
// left alone, so this never triggers the mermaid download by itself.
function rerenderMermaidDiagrams() {
    document.querySelectorAll('.mermaid-block[data-mermaid="done"]').forEach(block => {
        block.dataset.mermaid = 'pending';
        const figure = block.querySelector('.mermaid-figure');
        if (figure) figure.remove();
    });
    if (document.querySelector('.mermaid-block[data-mermaid="pending"]')) {
        renderMermaidBlocks(document);
    }
}

