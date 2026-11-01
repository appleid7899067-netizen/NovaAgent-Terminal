// channel/web/static/js/chat/ai-sources.js

class AISources {
    constructor(element) {
        this.container = element;
        this.button = element.querySelector('.sources-toggle');
        this.panel = element.querySelector('.sources-panel');
        this.stackItems = element.querySelectorAll('.source-item-stack');
        this.isOpen = false;
        this.isHovered = false;
        this.init();
    }

    init() {
        this.button.addEventListener('mouseenter', () => {
            this.isHovered = true;
            if (!this.isOpen) this.fanOut(true);
        });

        this.button.addEventListener('mouseleave', () => {
            this.isHovered = false;
            if (!this.isOpen) this.fanOut(false);
        });

        this.button.addEventListener('click', () => {
            this.isOpen = !this.isOpen;
            this.togglePanel();
        });
    }

    fanOut(fan) {
        this.stackItems.forEach((item, index) => {
            if (index === 0) return;
            const margin = fan ? '3px' : '-8px';
            item.style.marginLeft = margin;
        });
    }

    togglePanel() {
        const chevron = this.button.querySelector('.chevron-icon');
        const listItems = this.panel.querySelectorAll('li');
        
        if (this.isOpen) {
            chevron.style.transform = 'rotate(90deg)';
            this.fanOut(false);
            this.panel.style.gridTemplateRows = '1fr';
            this.panel.style.opacity = '1';
            this.panel.style.visibility = 'visible';
            this.button.setAttribute('aria-expanded', 'true');
            
            listItems.forEach((li, i) => {
                setTimeout(() => {
                    li.style.opacity = '1';
                    li.style.transform = 'translateY(0)';
                }, i * 50);
            });
        } else {
            chevron.style.transform = 'rotate(0deg)';
            this.panel.style.gridTemplateRows = '0fr';
            this.panel.style.opacity = '0';
            this.panel.style.visibility = 'hidden';
            this.button.setAttribute('aria-expanded', 'false');
            
            listItems.forEach(li => {
                li.style.opacity = '0';
                li.style.transform = 'translateY(8px)';
            });
        }
    }
}

window.renderAISources = function(sources) {
    if (!sources || sources.length === 0) return '';

    const stackLimit = 3;
    const stacked = sources.slice(0, stackLimit);
    const overflow = sources.length - stacked.length;

    const stackHtml = stacked.map((source, index) => `
        <div class="source-item-stack" 
             style="display:flex; align-items:center; justify-content:center; width:20px; height:20px; border-radius:50%; border:1px solid #4b5563; background:#1f2937; color:#d1d5db; overflow:hidden; transition:all 0.3s ease; z-index:${stacked.length - index}; ${index !== 0 ? 'margin-left:-8px;' : ''}">
            ${source.favicon ? `<img src="${source.favicon}" style="width:100%; height:100%; object-fit:cover;" />` : '<svg style="width:12px; height:12px;" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>'}
        </div>
    `).join('');

    const overflowHtml = overflow > 0 ? `<span style="margin-left:4px; font-size:12px; color:#9ca3af;">+${overflow}</span>` : '';

    const listHtml = sources.map(source => {
        let hostname = source.url;
        try { hostname = new URL(source.url).hostname.replace(/^www\./, ''); } catch(e) {}
        
        return `
            <li style="transform: translateY(8px); opacity: 0; transition: all 0.3s ease;">
                <a href="${source.url}" target="_blank" rel="noopener noreferrer" style="display:flex; align-items:flex-start; gap:10px; border-radius:8px; padding:6px 4px; text-decoration:none; transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='transparent'">
                    <div style="margin-top:2px; display:flex; align-items:center; justify-content:center; width:20px; height:20px; border-radius:50%; border:1px solid #4b5563; background:#1f2937; flex-shrink:0;">
                        ${source.favicon ? `<img src="${source.favicon}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;" />` : '<svg style="width:12px; height:12px; color:#9ca3af;" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>'}
                    </div>
                    <div style="min-width:0;">
                        <div style="display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:500; color:#e5e7eb; font-size:14px;">${source.title}</div>
                        <div style="display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#9ca3af; font-size:12px;">${source.snippet || hostname}</div>
                    </div>
                </a>
            </li>
        `;
    }).join('');

    return `
        <div class="ai-sources" id="ai-sources-${Date.now()}" style="width:100%; margin:8px 0;">
            <button class="sources-toggle" aria-expanded="false" type="button" style="display:flex; cursor:pointer; align-items:center; gap:8px; border-radius:8px; padding:4px 0; color:#9ca3af; font-size:14px; background:transparent; border:none; outline:none; transition: color 0.2s;" onmouseover="this.style.color='#e5e7eb'" onmouseout="this.style.color='#9ca3af'">
                <div style="display:flex; align-items:center;">
                    ${stackHtml}
                    ${overflowHtml}
                </div>
                <span>Sources</span>
                <svg class="chevron-icon" style="width:16px; height:16px; transition: transform 0.3s;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
            </button>

            <div class="sources-panel" style="display:grid; grid-template-rows: 0fr; opacity: 0; visibility: hidden; transition: all 0.3s ease-in-out;">
                <ul style="margin-top:4px; list-style:none; overflow:hidden; padding-left:4px; margin-bottom:0; padding-right:4px;">
                    ${listHtml}
                </ul>
            </div>
        </div>
    `;
};
