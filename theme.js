/**
 * theme.js — Light/Dark mode toggle with localStorage persistence.
 * Include this file at the end of <body> on every page.
 * Place the inline init snippet in <head> to prevent flash of unstyled content.
 */

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
        localStorage.setItem('theme', theme);
    } catch (e) {
        // Gracefully degrade when storage is blocked (private/restricted modes).
    }
    var btn = document.getElementById('theme-toggle');
    if (btn) {
        var isDark = theme === 'dark';
        btn.textContent = isDark ? '☀' : '☾';
        btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
        btn.setAttribute('aria-label', btn.title);
    }
}

function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('theme-toggle');
    if (btn) {
        btn.addEventListener('click', toggleTheme);
        // Sync button label with currently active theme
        var current = document.documentElement.getAttribute('data-theme') || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        applyTheme(current);
    }
});
