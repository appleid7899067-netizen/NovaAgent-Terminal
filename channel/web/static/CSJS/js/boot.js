/* Startup: theme, i18n, auth gate, initial fetches. Loads last.
   Split out of console.js. These are classic scripts sharing one global
   scope; see channel/web/README.md before changing the load order. */

// Everything below reads protected endpoints, so it waits for the auth gate:
// fired before login it only collects 401s, and the login path never retries
// it, which left the chat empty after signing in until the next reload.
requestAuthGatedStart(loadAgentCatalog);
requestAuthGatedStart(() => {
    fetch('/config').then(r => r.json()).then(data => {
        if (data.status === 'success') {
            appConfig = data;
            const title = data.title || 'boss.slilelo';
            document.getElementById('welcome-title').textContent = title;
            initConfigView(data);
        }
        loadHistory(1);
    }).catch(() => { loadHistory(1); });
});

// Start polling so scheduler/push messages are received.
requestAuthGatedStart(startPolling);
// =====================================================================
// Initialization
// =====================================================================
applyTheme();
applyI18n();

fetch('/auth/check').then(r => r.json()).then(data => {
    if (data.auth_required && !data.authenticated) {
        // Keep background pollers parked until login succeeds (openAuthGate is
        // called from the login handler), so they don't spam 401s meanwhile.
        showLoginScreen();
    } else {
        if (data.auth_required) {
            const logoutBtn = document.getElementById('logout-btn-header');
            if (logoutBtn) logoutBtn.classList.remove('hidden');
        }
        openAuthGate();
        initApp();
    }
}).catch(() => {
    // No auth info available (e.g. request failed): fall back to running so a
    // password-less deployment still works.
    openAuthGate();
    initApp();
});

requestAnimationFrame(() => {
    document.body.classList.add('transition-colors', 'duration-200');
});


// === Bolt Style Chat Auto-Mount ===
(function() {
  function tryMountBolt() {
    if (typeof BoltStyleChat === 'undefined') return false;
    const ws = document.getElementById('welcome-screen');
    if (!ws) return false;
    
    const root = document.createElement('div');
    root.id = 'bolt-chat-root';
    ws.replaceWith(root);
    
    BoltStyleChat.mount('#bolt-chat-root', {
      onSend: (text, model) => {
        console.log('📤 BoltChat ส่ง:', text, '| Model:', model.name);
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
          chatInput.value = text;
          chatInput.dispatchEvent(new Event('input', { bubbles: true }));
          const sendBtn = document.querySelector('[data-send-btn], #send-btn, .send-btn');
          if (sendBtn) sendBtn.click();
        }
      },
      onImport: (source) => console.log('📥 Import:', source),
      onModelChange: (model) => console.log('🔄 Model:', model.name)
    });
    console.log('✅ BoltStyleChat auto-mounted');
    return true;
  }
  
  // ลอง mount หลัง boot 3 วิ
  setTimeout(tryMountBolt, 3000);
})();
