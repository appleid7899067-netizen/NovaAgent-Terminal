/**
 * Voice Reader — อ่านข้อความ AI ด้วยเสียง (Web Speech API)
 * ไม่ต้อง Termux:API — ใช้ built-in browser
 */

(function() {
    'use strict';
    
    const CONFIG = {
        lang: 'th-TH',
        rate: 1.0,
        pitch: 1.0,
        volume: 1.0,
        autoRead: false
    };
    
    let autoReadEnabled = CONFIG.autoRead;
    
    // === Speak ===
    function speak(text) {
        if (!text || !('speechSynthesis' in window)) return;
        speechSynthesis.cancel();
        
        const u = new SpeechSynthesisUtterance(text);
        u.lang = CONFIG.lang;
        u.rate = CONFIG.rate;
        u.pitch = CONFIG.pitch;
        u.volume = CONFIG.volume;
        speechSynthesis.speak(u);
        
        console.log('🔊 Speaking:', text.substring(0, 50));
    }
    
    function stop() {
        if ('speechSynthesis' in window) speechSynthesis.cancel();
    }
    
    // === Add 🔊 Button to Message ===
    function addSpeakButton(msgEl) {
        if (!msgEl || msgEl.querySelector('.speak-btn')) return;
        
        const text = msgEl.textContent || msgEl.innerText;
        if (!text || text.length < 3) return;
        
        const btn = document.createElement('button');
        btn.className = 'speak-btn';
        btn.title = 'อ่านด้วยเสียง';
        btn.innerHTML = '🔊';
        btn.style.cssText = 'background:none;border:none;cursor:pointer;padding:2px 6px;font-size:14px;opacity:0.5;transition:opacity 0.2s;';
        btn.onmouseenter = () => btn.style.opacity = '1';
        btn.onmouseleave = () => btn.style.opacity = '0.5';
        btn.onclick = (e) => { e.stopPropagation(); speak(text); };
        
        msgEl.appendChild(btn);
    }
    
    // === Observer ===
    function observe() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(m => {
                m.addedNodes.forEach(node => {
                    if (node.nodeType !== 1) return;
                    
                    // หา bot messages
                    const bots = node.matches && node.matches('[class*="bot-message"], [class*="assistant"]')
                        ? [node]
                        : (node.querySelectorAll ? node.querySelectorAll('[class*="bot-message"], [class*="assistant"]') : []);
                    
                    bots.forEach(bot => {
                        addSpeakButton(bot);
                        
                        if (autoReadEnabled) {
                            const text = bot.textContent;
                            if (text && text.length > 10) {
                                setTimeout(() => speak(text), 800);
                            }
                        }
                    });
                });
            });
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
        console.log('✅ Voice Reader: started');
    }
    
    // === API ===
    window.novaVoice = {
        speak,
        stop,
        toggleAutoRead: () => {
            autoReadEnabled = !autoReadEnabled;
            console.log('🔊 Auto-read:', autoReadEnabled ? 'ON' : 'OFF');
            return autoReadEnabled;
        },
        isAutoRead: () => autoReadEnabled,
        config: CONFIG
    };
    
    // === Init ===
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', observe);
    } else {
        observe();
    }
    
    console.log('✅ Voice Reader loaded');
    console.log('💡 window.novaVoice.speak("ทดสอบ")');
    console.log('💡 window.novaVoice.toggleAutoRead()');
})();
