// Tiny placeholder script for demo site

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.nav-desktop');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const visible = nav.style.display !== 'none';
      nav.style.display = visible ? 'none' : 'flex';
    });
  }
  // Theme persistence
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    themeToggle.textContent = current === 'dark' ? '🌗' : '🌞';
    themeToggle.addEventListener('click', () => {
      const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      themeToggle.textContent = newTheme === 'dark' ? '🌗' : '🌞';
      localStorage.setItem('na-theme', newTheme);
    });
  }
  // Load saved theme
  const saved = localStorage.getItem('na-theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
    if (themeToggle) themeToggle.textContent = saved === 'dark' ? '🌗' : '🌞';
  }
});
