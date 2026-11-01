/* Bolt Style Chat - Vanilla JS Component */
(function() {
  'use strict';

  // === Models Data ===
  const MODELS = [
    { id: 'sonnet-4.5', name: 'Sonnet 4.5', description: 'Fast & intelligent', icon: 'fa-bolt', color: 'text-blue-400', badge: 'Default' },
    { id: 'opus-4.5', name: 'Opus 4.5', description: 'Most capable', icon: 'fa-wand-magic-sparkles', color: 'text-purple-400', badge: 'Pro' },
    { id: 'haiku-4.5', name: 'Haiku 4.5', description: 'Lightning fast', icon: 'fa-brain', color: 'text-emerald-400' },
    { id: 'gpt-4o', name: 'GPT-4o', description: 'OpenAI flagship', icon: 'fa-star', color: 'text-green-400' },
    { id: 'gemini-2.0', name: 'Gemini 2.0', description: 'Google AI', icon: 'fa-gem', color: 'text-cyan-400' }
  ];

  // === State ===
  let state = {
    selectedModel: MODELS[0],
    message: '',
    showAttachMenu: false,
    showModelMenu: false
  };

  // === Render Announcement Badge ===
  function renderAnnouncement(text, href) {
    const isLink = href && href !== '#';
    const tag = isLink ? 'a' : 'button';
    const attrs = isLink ? `href="${href}" target="_blank" rel="noopener noreferrer"` : '';
    return `
      <${tag} ${attrs} class="bolt-announcement-badge">
        <i class="fas fa-bolt" style="font-size:16px"></i>
        <span style="font-weight:500">${text}</span>
      </${tag}>
    `;
  }

  // === Render Model Selector ===
  function renderModelSelector() {
    const items = MODELS.map(m => `
      <button class="bolt-model-item ${state.selectedModel.id === m.id ? 'active' : ''}" data-model-id="${m.id}">
        <i class="fas ${m.icon} ${m.color}" style="font-size:14px;width:16px"></i>
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:13px;font-weight:500">${m.name}</span>
            ${m.badge ? `<span class="bolt-badge bolt-badge-${m.badge.toLowerCase()}">${m.badge}</span>` : ''}
          </div>
          <span style="font-size:11px;color:#6a6a6f">${m.description}</span>
        </div>
        ${state.selectedModel.id === m.id ? '<i class="fas fa-check" style="color:#60a5fa;font-size:14px"></i>' : ''}
      </button>
    `).join('');

    return `
      <div style="position:relative" id="modelSelectorWrap">
        <button class="bolt-model-btn" id="modelSelectorBtn">
          <i class="fas ${state.selectedModel.icon} ${state.selectedModel.color}" style="font-size:14px"></i>
          <span>${state.selectedModel.name}</span>
          <i class="fas fa-chevron-down" style="font-size:12px;transition:transform 0.2s"></i>
        </button>
        ${state.showModelMenu ? `
          <div class="bolt-model-menu">
            <div style="padding:6px">
              <div style="padding:6px 10px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#5a5a5f">
                Select Model
              </div>
              ${items}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  // === Render Attach Menu ===
  function renderAttachMenu() {
    if (!state.showAttachMenu) return '';
    const items = [
      { icon: 'fa-paperclip', label: 'Upload file' },
      { icon: 'fa-image', label: 'Add image' },
      { icon: 'fa-file-code', label: 'Import code' }
    ];
    return `
      <div style="position:absolute;bottom:100%;left:0;margin-bottom:8px;min-width:180px;background:rgba(26,26,30,0.95);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.1);border-radius:12px;box-shadow:0 20px 40px rgba(0,0,0,0.5);overflow:hidden;z-index:50">
        <div style="padding:6px">
          ${items.map(it => `
            <button class="bolt-model-item" data-attach="${it.label}">
              <i class="fas ${it.icon}" style="font-size:14px"></i>
              <span style="font-size:13px">${it.label}</span>
            </button>
          `).join('')}
        </div>
      </div>
    `;
  }

  // === Main Render ===
  function render() {
    const title = 'What will you';
    const subtitle = 'Create stunning apps & websites by chatting with AI.';
    const announcement = 'Introducing Bolt V2';
    const placeholder = 'What do you want to build?';

    return `
      <div class="bolt-container">
        <div class="bolt-ray-bg">
          <div class="bolt-ray-glow"></div>
        </div>

        <div style="position:absolute;top:70px;left:50%;transform:translateX(-50%);z-index:20">
          ${renderAnnouncement(announcement, '#')}
        </div>

        <div class="bolt-content">
          <div style="text-align:center;margin-bottom:24px">
            <h1 style="font-size:36px;font-weight:700;color:white;letter-spacing:-0.02em;margin-bottom:4px;line-height:1.2">
              ${title} <span class="bolt-title-gradient">build</span> today?
            </h1>
            <p style="font-size:16px;font-weight:600;color:#8a8a8f;margin:0">${subtitle}</p>
          </div>

          <div class="bolt-input-wrap">
            <div class="bolt-input-inner">
              <textarea 
                id="boltChatInput"
                class="bolt-textarea"
                placeholder="${placeholder}"
                rows="1"
              ></textarea>
              <div class="bolt-input-footer">
                <div style="display:flex;align-items:center;gap:4px">
                  <div style="position:relative">
                    <button id="boltPlusBtn" class="bolt-plus-btn">
                      <i class="fas fa-plus" style="font-size:14px;transition:transform 0.2s"></i>
                    </button>
                    ${renderAttachMenu()}
                  </div>
                  ${renderModelSelector()}
                </div>
                <div style="display:flex;align-items:center;gap:8px">
                  <button style="display:flex;align-items:center;gap:6px;padding:8px 12px;border-radius:9999px;font-size:12px;font-weight:500;color:#6a6a6f;background:transparent;border:none;cursor:pointer">
                    <i class="fas fa-lightbulb" style="font-size:14px"></i>
                    <span>Plan</span>
                  </button>
                  <button id="boltSendBtn" class="bolt-send-btn" disabled>
                    <span>Build now</span>
                    <i class="fas fa-paper-plane" style="font-size:14px"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:16px;justify-content:center">
            <span style="font-size:13px;color:#6a6a6f">or import from</span>
            <div style="display:flex;gap:8px">
              <button class="bolt-import-btn" data-import="figma">
                <i class="fas fa-palette" style="font-size:14px"></i>
                <span>Figma</span>
              </button>
              <button class="bolt-import-btn" data-import="github">
                <i class="fab fa-github" style="font-size:14px"></i>
                <span>GitHub</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // === Mount ===
  window.BoltStyleChat = {
    mount: function(selector, options = {}) {
      const container = document.querySelector(selector);
      if (!container) {
        console.error('BoltStyleChat: container not found:', selector);
        return;
      }

      function refresh() {
        container.innerHTML = render();
        bindEvents();
      }

      function bindEvents() {
        // Textarea
        const textarea = container.querySelector('#boltChatInput');
        const sendBtn = container.querySelector('#boltSendBtn');
        if (textarea) {
          textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
            if (sendBtn) sendBtn.disabled = !textarea.value.trim();
          });
          textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              if (textarea.value.trim()) handleSend(textarea.value);
            }
          });
        }

        // Send
        if (sendBtn) {
          sendBtn.addEventListener('click', () => {
            if (textarea && textarea.value.trim()) handleSend(textarea.value);
          });
        }

        // Plus button
        const plusBtn = container.querySelector('#boltPlusBtn');
        if (plusBtn) {
          plusBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            state.showAttachMenu = !state.showAttachMenu;
            state.showModelMenu = false;
            refresh();
          });
        }

        // Model selector
        const modelBtn = container.querySelector('#modelSelectorBtn');
        if (modelBtn) {
          modelBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            state.showModelMenu = !state.showModelMenu;
            state.showAttachMenu = false;
            refresh();
          });
        }

        // Model items
        container.querySelectorAll('[data-model-id]').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-model-id');
            const model = MODELS.find(m => m.id === id);
            if (model) {
              state.selectedModel = model;
              state.showModelMenu = false;
              refresh();
              if (options.onModelChange) options.onModelChange(model);
            }
          });
        });

        // Attach items
        container.querySelectorAll('[data-attach]').forEach(btn => {
          btn.addEventListener('click', () => {
            const action = btn.getAttribute('data-attach');
            state.showAttachMenu = false;
            refresh();
            console.log('Attach:', action);
          });
        });

        // Import buttons
        container.querySelectorAll('[data-import]').forEach(btn => {
          btn.addEventListener('click', () => {
            const source = btn.getAttribute('data-import');
            console.log('Import:', source);
            if (options.onImport) options.onImport(source);
          });
        });

        // Close menus on outside click
        container.addEventListener('click', (e) => {
          if (!e.target.closest('#modelSelectorWrap') && !e.target.closest('#boltPlusBtn')) {
            if (state.showModelMenu || state.showAttachMenu) {
              state.showModelMenu = false;
              state.showAttachMenu = false;
              refresh();
            }
          }
        });
      }

      function handleSend(text) {
        console.log('Send:', text, 'Model:', state.selectedModel.name);
        if (options.onSend) {
          options.onSend(text, state.selectedModel);
        }
        // Reset
        const textarea = container.querySelector('#boltChatInput');
        if (textarea) {
          textarea.value = '';
          textarea.style.height = 'auto';
        }
        const sendBtn = container.querySelector('#boltSendBtn');
        if (sendBtn) sendBtn.disabled = true;
      }

      refresh();
      console.log('✅ BoltStyleChat mounted');
    }
  };

  console.log('✅ BoltStyleChat loaded');
  console.log('💡 ใช้: BoltStyleChat.mount("#selector")');
})();
