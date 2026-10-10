/**
 * FoxVC Mobile-First Visual Jigsaw Studio
 * Pure FoxVC Game/Logic blocks, native touch drag, zero popups.
 */

class FoxVCLexer {
  constructor(src) {
    this.src = src;
    this.pos = 0;
  }
  tokenize() {
    const tokens = [];
    while (this.pos < this.src.length) {
      const ch = this.src[this.pos];
      if (ch === ' ' || ch === '\t' || ch === '\r' || ch === '\n') { this.pos++; continue; }
      if (ch === '#') {
        while (this.pos < this.src.length && this.src[this.pos] !== '\n') this.pos++;
        continue;
      }
      if (ch === '"' || ch === "'") {
        const quote = ch;
        let str = '';
        this.pos++;
        while (this.pos < this.src.length && this.src[this.pos] !== quote) {
          str += this.src[this.pos];
          this.pos++;
        }
        this.pos++;
        tokens.push({ type: 'STRING', val: str });
        continue;
      }
      if (/[0-9]/.test(ch) || (ch === '-' && /[0-9]/.test(this.src[this.pos + 1]))) {
        let num = '';
        while (this.pos < this.src.length && /[0-9.-]/.test(this.src[this.pos])) {
          num += this.src[this.pos];
          this.pos++;
        }
        tokens.push({ type: 'NUMBER', val: parseFloat(num) });
        continue;
      }
      if (/[a-zA-Z_]/.test(ch)) {
        let ident = '';
        while (this.pos < this.src.length && /[a-zA-Z0-9_]/.test(this.src[this.pos])) {
          ident += this.src[this.pos];
          this.pos++;
        }
        tokens.push({ type: 'IDENT', val: ident });
        continue;
      }
      if ('=+-*/><!(),:[]{}'.indexOf(ch) !== -1) {
        tokens.push({ type: 'SYMBOL', val: ch });
        this.pos++;
        continue;
      }
      this.pos++;
    }
    return tokens;
  }
}

class VisualLearningMode {
  constructor(container, callbacks = {}) {
    this.container = container;
    this.callbacks = callbacks;
    this.blocks = [];
    this.counter = 0;
    this.activeDrag = null;
    this.dragOffset = { x: 0, y: 0 };
    this.pan = { x: 20, y: 20 };
    this._initDOM();
  }

  _initDOM() {
    this.container.innerHTML = `
      <div id="vlm-board-wrap">
        <!-- Visual Action Toolbar (Mobile-friendly) -->
        <div class="vlm-top-bar">
          <div style="display:flex;align-items:center;gap:6px;overflow-x:auto;">
            <button id="vlm-btn-import" class="vlm-btn vlm-btn-gold">📥 Sync From Code</button>
            <button id="vlm-btn-run" class="vlm-btn vlm-btn-green">▶ Run Blocks</button>
            <button id="vlm-btn-clear" class="vlm-btn vlm-btn-gray">Clear</button>
          </div>
          <button id="vlm-btn-back" class="vlm-btn vlm-btn-back">⬅ Coding</button>
        </div>

        <!-- Horizontal Swipeable Card Palette -->
        <div class="vlm-drawer">
          <div class="vlm-card" data-type="space">🌌 space</div>
          <div class="vlm-card" data-type="background">🎨 background</div>
          <div class="vlm-card" data-type="actor">👾 actor</div>
          <div class="vlm-card" data-type="motion">🚀 velocity</div>
          <div class="vlm-card" data-type="bounce">🛡️ bounce</div>
          <div class="vlm-card" data-type="on_tick">⏱️ on tick</div>
          <div class="vlm-card" data-type="on_key">🎮 on key</div>
          <div class="vlm-card" data-type="state">📦 state</div>
          <div class="vlm-card" data-type="when">⚡ when</div>
          <div class="vlm-card" data-type="say">🗣️ say</div>
        </div>

        <!-- Touch Sandbox Area -->
        <div id="vlm-touch-canvas">
          <div id="vlm-canvas-plane"></div>
          <!-- Diagnostic popup inside canvas -->
          <div id="vlm-err-callout" class="vlm-err-callout"></div>
        </div>
      </div>
    `;

    this.canvasWrap = document.getElementById('vlm-touch-canvas');
    this.plane = document.getElementById('vlm-canvas-plane');
    this.errBox = document.getElementById('vlm-err-callout');

    this._injectStyles();
    this._attachEvents();
  }

  _injectStyles() {
    if (document.getElementById('vlm-custom-style')) return;
    const st = document.createElement('style');
    st.id = 'vlm-custom-style';
    st.innerHTML = `
      #vlm-board-wrap {
        width: 100%; height: 100%; display: flex; flex-direction: column;
        background: #090603; overflow: hidden; position: relative;
      }
      .vlm-top-bar {
        background: #19110a; border-bottom: 1px solid #332214;
        padding: 6px 10px; display: flex; align-items: center; justify-content: space-between;
        gap: 6px; flex-shrink: 0;
      }
      .vlm-btn {
        border: none; border-radius: 4px; padding: 6px 10px; font-size: 11px; font-weight: 700;
        cursor: pointer; white-space: nowrap; touch-action: manipulation;
      }
      .vlm-btn-gold { background: #d97706; color: #fff; }
      .vlm-btn-green { background: #16a34a; color: #fff; }
      .vlm-btn-gray { background: #26190f; color: #fed7aa; border: 1px solid #3e2b1c; }
      .vlm-btn-back { background: #f97316; color: #fff; }

      .vlm-drawer {
        background: #120c07; border-bottom: 1px solid #2e1d10;
        display: flex; gap: 8px; padding: 6px 10px; overflow-x: auto;
        -webkit-overflow-scrolling: touch; flex-shrink: 0;
      }
      .vlm-card {
        background: #1e140c; border: 1px solid #3d2817; color: #fed7aa;
        padding: 6px 12px; border-radius: 5px; font-size: 11px; font-weight: 700;
        cursor: pointer; white-space: nowrap; user-select: none; touch-action: manipulation;
      }
      .vlm-card:active { background: #f97316; color: #fff; }

      #vlm-touch-canvas {
        flex: 1; position: relative; overflow: hidden; touch-action: none;
        background: #070503;
        background-image: radial-gradient(#26180c 1.5px, transparent 1.5px);
        background-size: 20px 20px;
      }
      #vlm-canvas-plane {
        position: absolute; inset: 0; width: 3000px; height: 3000px;
      }

      .vlm-err-callout {
        display: none; position: absolute; top: 10px; left: 10px; right: 10px;
        background: rgba(80, 15, 10, 0.95); border: 1px solid #ef4444; color: #fee2e2;
        padding: 8px 12px; border-radius: 6px; font-size: 11px; z-index: 100;
      }

      /* Touch Jigsaw Blocks */
      .vlm-puzzle-tile {
        position: absolute; border-radius: 6px; user-select: none;
        box-shadow: 0 4px 10px rgba(0,0,0,0.6); touch-action: none; cursor: grab;
      }
      .vlm-tile-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 6px 8px; font-weight: 800; font-size: 11px; gap: 6px;
      }
      .vlm-tile-header input {
        background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.3);
        color: #fff; border-radius: 3px; padding: 2px 4px; font-size: 11px; font-weight: 600;
      }
      .vlm-tile-del {
        padding: 2px 6px; font-weight: bold; cursor: pointer; color: rgba(255,255,255,0.6);
      }
      .vlm-tile-del:active { color: #ef4444; }

      /* Female notch on top */
      .vlm-peg-in {
        position: absolute; top: -3px; left: 24px; width: 22px; height: 6px;
        background: #070503; border-radius: 0 0 4px 4px; border-bottom: 2px solid rgba(255,255,255,0.4);
      }
      /* Male tab on bottom */
      .vlm-peg-out {
        position: absolute; bottom: -6px; left: 24px; width: 22px; height: 6px;
        background: inherit; border-radius: 0 0 4px 4px; border: 2px solid rgba(255,255,255,0.4); border-top: none;
      }
      /* Container Jaw */
      .vlm-jaw-slot {
        min-height: 40px; margin-left: 14px; background: rgba(0,0,0,0.3);
        border-left: 3px dashed rgba(255,255,255,0.3); padding: 4px;
        font-size: 9px; color: rgba(255,255,255,0.4); font-style: italic;
      }
    `;
    document.head.appendChild(st);
  }

  _attachEvents() {
    // Back button switches right to Coding tab
    document.getElementById('vlm-btn-back').addEventListener('click', () => {
      if (this.callbacks.onGoCoding) this.callbacks.onGoCoding();
    });

    // Clear board
    document.getElementById('vlm-btn-clear').addEventListener('click', () => {
      this.blocks.forEach(b => b.el.remove());
      this.blocks = [];
      this.errBox.style.display = 'none';
    });

    // Run game from blocks
    document.getElementById('vlm-btn-run').addEventListener('click', () => this.runFromBlocks());

    // Import from current editor code
    document.getElementById('vlm-btn-import').addEventListener('click', () => {
      if (this.callbacks.getCode) {
        this.parseCodeToBlocks(this.callbacks.getCode());
      }
    });

    // Palette item tap/click
    this.container.querySelectorAll('.vlm-card').forEach(card => {
      card.addEventListener('click', () => {
        const type = card.dataset.type;
        const x = 20 + (Math.random() * 40);
        const y = 20 + (Math.random() * 60);
        this.addBlock(type, x, y);
      });
    });

    // Universal Pointer/Touch Dragging
    const handleMove = (clientX, clientY) => {
      if (!this.activeDrag) return;
      const rect = this.canvasWrap.getBoundingClientRect();
      let x = clientX - rect.left - this.dragOffset.x;
      let y = clientY - rect.top - this.dragOffset.y;

      x = Math.max(4, x);
      y = Math.max(4, y);

      this.activeDrag.x = x;
      this.activeDrag.y = y;
      this.activeDrag.el.style.left = `${x}px`;
      this.activeDrag.el.style.top = `${y}px`;

      this._checkProximity(this.activeDrag);
    };

    const handleEnd = () => {
      if (this.activeDrag) {
        this.activeDrag.el.style.zIndex = "10";
        this._applySnap(this.activeDrag);
        this.activeDrag = null;
      }
    };

    // Desktop Mouse
    window.addEventListener('mousemove', e => handleMove(e.clientX, e.clientY));
    window.addEventListener('mouseup', handleEnd);

    // Mobile / Tablet Touch
    this.canvasWrap.addEventListener('touchmove', e => {
      if (!this.activeDrag) return;
      e.preventDefault(); // Stop mobile screen scrolling while dragging block
      const t = e.touches[0];
      handleMove(t.clientX, t.clientY);
    }, { passive: false });

    window.addEventListener('touchend', handleEnd);
  }

  addBlock(type, x, y, initialParams = {}) {
    const id = ++this.counter;
    const el = document.createElement('div');
    el.className = 'vlm-puzzle-tile';
    el.id = `vlm-tile-${id}`;
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;

    const b = { id, type, x, y, el, parent: null, next: null, nested: null, params: { ...initialParams } };

    let color = "#0284c7";
    let border = "#38bdf8";
    let isContainer = false;
    let title = "";
    let inputs = "";

    // PURE FOXVC SPECS
    if (type === 'space') {
      color = "#9a3412"; border = "#f97316"; isContainer = true; title = "🌌 space";
      b.params.name = b.params.name || "World";
      inputs = `<input data-k="name" value="${b.params.name}" style="width:65px;"> [800, 600]`;
    } else if (type === 'background') {
      color = "#78350f"; border = "#d97706"; title = "🎨 background";
      b.params.color = b.params.color || "#090d16";
      inputs = `<input data-k="color" value="${b.params.color}" style="width:70px;">`;
    } else if (type === 'actor') {
      color = "#9333ea"; border = "#c084fc"; isContainer = true; title = "👾 actor";
      b.params.name = b.params.name || "Hero";
      b.params.x = b.params.x || 120;
      b.params.y = b.params.y || 240;
      inputs = `<input data-k="name" value="${b.params.name}" style="width:50px;"> [${b.params.x}, ${b.params.y}]`;
    } else if (type === 'motion') {
      color = "#4338ca"; border = "#818cf8"; title = "🚀 velocity";
      b.params.vx = b.params.vx || 8;
      b.params.vy = b.params.vy || 0;
      inputs = `vx: <input data-k="vx" type="number" value="${b.params.vx}" style="width:34px;">`;
    } else if (type === 'bounce') {
      color = "#3730a3"; border = "#6366f1"; title = "🛡️ bounce";
      b.params.val = b.params.val || 0.8;
      inputs = `<input data-k="val" type="number" step="0.1" value="${b.params.val}" style="width:40px;">`;
    } else if (type === 'on_tick') {
      color = "#c2410c"; border = "#fb923c"; isContainer = true; title = "⏱️ on tick";
      inputs = `do`;
    } else if (type === 'on_key') {
      color = "#ea580c"; border = "#fdba74"; isContainer = true; title = "🎮 on key";
      b.params.key = b.params.key || "Space";
      inputs = `<input data-k="key" value="${b.params.key}" style="width:50px;"> do`;
    } else if (type === 'state') {
      color = "#0369a1"; border = "#38bdf8"; title = "📦 state";
      b.params.var = b.params.var || "score";
      b.params.val = b.params.val || "100";
      inputs = `<input data-k="var" value="${b.params.var}" style="width:45px;"> = <input data-k="val" value="${b.params.val}" style="width:45px;">`;
    } else if (type === 'when') {
      color = "#0284c7"; border = "#7dd3fc"; isContainer = true; title = "⚡ when";
      b.params.cond = b.params.cond || "score > 50";
      inputs = `<input data-k="cond" value="${b.params.cond}" style="width:75px;"> then`;
    } else if (type === 'say') {
      color = "#059669"; border = "#34d399"; title = "🗣️ say";
      b.params.msg = b.params.msg || "FoxVC Active";
      inputs = `<input data-k="msg" value="${b.params.msg}" style="width:90px;">`;
    }

    el.style.background = color;
    el.style.border = `2px solid ${border}`;

    const topPeg = `<div class="vlm-peg-in"></div>`;
    const bottomPeg = `<div class="vlm-peg-out" style="background:${color};"></div>`;
    const jawSlot = isContainer ? `<div class="vlm-jaw-slot">⮞ Nest child puzzle block here</div>` : '';

    el.innerHTML = `
      ${topPeg}
      <div class="vlm-tile-header">
        <div style="display:flex;align-items:center;gap:5px;">
          <span>${title}</span>
          ${inputs}
        </div>
        <span class="vlm-tile-del">✕</span>
      </div>
      ${jawSlot}
      ${bottomPeg}
    `;

    // Input handlers
    el.querySelectorAll('input').forEach(inp => {
      inp.addEventListener('input', e => {
        b.params[e.target.dataset.k] = e.target.value;
      });
    });

    // Delete
    el.querySelector('.vlm-tile-del').addEventListener('click', () => {
      this.blocks = this.blocks.filter(x => x.id !== b.id);
      el.remove();
    });

    // Touch / Click Drag initiation
    const startDrag = (cx, cy) => {
      if (b.parent) { b.parent.next = null; b.parent = null; }
      this.activeDrag = b;
      el.style.zIndex = "1000";
      const r = el.getBoundingClientRect();
      this.dragOffset = { x: cx - r.left, y: cy - r.top };
    };

    el.addEventListener('mousedown', e => {
      if (e.target.tagName === 'INPUT' || e.target.classList.contains('vlm-tile-del')) return;
      startDrag(e.clientX, e.clientY);
    });

    el.addEventListener('touchstart', e => {
      if (e.target.tagName === 'INPUT' || e.target.classList.contains('vlm-tile-del')) return;
      const t = e.touches[0];
      startDrag(t.clientX, t.clientY);
    }, { passive: true });

    this.plane.appendChild(el);
    this.blocks.push(b);
    return b;
  }

  _checkProximity(active) {
    const snapDist = 28;
    for (const b of this.blocks) {
      if (b.id === active.id) continue;
      const targetY = b.y + b.el.offsetHeight - 4;
      if (Math.abs(active.x - b.x) < 30 && Math.abs(active.y - targetY) < snapDist) {
        active.el.style.filter = "drop-shadow(0 0 12px #f97316)";
        return;
      }
    }
    active.el.style.filter = "drop-shadow(0 4px 10px rgba(0,0,0,0.6))";
  }

  _applySnap(active) {
    const snapDist = 28;
    for (const b of this.blocks) {
      if (b.id === active.id) continue;
      const targetY = b.y + b.el.offsetHeight - 4;
      if (Math.abs(active.x - b.x) < 30 && Math.abs(active.y - targetY) < snapDist) {
        active.x = b.x;
        active.y = targetY;
        active.el.style.left = `${active.x}px`;
        active.el.style.top = `${active.y}px`;
        b.next = active;
        active.parent = b;
        active.el.style.filter = "drop-shadow(0 0 10px #22c55e)";
        return;
      }
    }
    active.el.style.filter = "drop-shadow(0 4px 10px rgba(0,0,0,0.6))";
  }

  // --- Parse text code directly into blocks on the canvas ---
  parseCodeToBlocks(src) {
    if (!src || !src.trim()) return;
    this.blocks.forEach(b => b.el.remove());
    this.blocks = [];

    const lexer = new FoxVCLexer(src);
    const tokens = lexer.tokenize();

    let curX = 24;
    let curY = 24;

    for (let i = 0; i < tokens.length; i++) {
      const t = tokens[i];
      if (t.type === 'IDENT') {
        const cmd = t.val.toLowerCase();
        if (cmd === 'space') {
          const name = (tokens[i + 1] && tokens[i + 1].type === 'IDENT') ? tokens[++i].val : "World";
          this.addBlock('space', curX, curY, { name });
          curY += 75;
        } else if (cmd === 'background') {
          const color = (tokens[i + 1] && tokens[i + 1].type === 'STRING') ? tokens[++i].val : "#090d16";
          this.addBlock('background', curX, curY, { color });
          curY += 45;
        } else if (cmd === 'actor') {
          const name = (tokens[i + 1] && tokens[i + 1].type === 'IDENT') ? tokens[++i].val : "Hero";
          this.addBlock('actor', curX, curY, { name, x: 120, y: 240 });
          curY += 75;
        } else if (cmd === 'state') {
          const v = (tokens[i + 1] && tokens[i + 1].type === 'IDENT') ? tokens[++i].val : "score";
          let val = "100";
          if (tokens[i + 1] && tokens[i + 1].val === '=') { i += 2; val = tokens[i] ? tokens[i].val : "100"; }
          this.addBlock('state', curX, curY, { var: v, val });
          curY += 45;
        } else if (cmd === 'say') {
          const msg = (tokens[i + 1] && tokens[i + 1].type === 'STRING') ? tokens[++i].val : "Running";
          this.addBlock('say', curX, curY, { msg });
          curY += 45;
        } else if (cmd === 'on') {
          const ev = (tokens[i + 1] && tokens[i + 1].type === 'IDENT') ? tokens[++i].val.toLowerCase() : "tick";
          if (ev === 'tick') {
            this.addBlock('on_tick', curX, curY);
            curY += 75;
          } else if (ev === 'key') {
            const k = (tokens[i + 1] && tokens[i + 1].type === 'STRING') ? tokens[++i].val : "Space";
            this.addBlock('on_key', curX, curY, { key: k });
            curY += 75;
          }
        }
      }
    }
  }

  // --- Run blocks directly and route straight to Output tab ---
  async runFromBlocks() {
    this.errBox.style.display = 'none';
    if (this.blocks.length === 0) {
      this.errBox.innerText = "⚠️ No blocks on canvas. Tap the cards above to add some.";
      this.errBox.style.display = 'block';
      return;
    }

    // Pure FoxVC Assembly (Zero Python)
    const lines = ['# --- FoxVC Native Execution ---'];
    for (const b of this.blocks) {
      if (b.type === 'space') lines.push(`space ${b.params.name || 'World'} [800, 600]`);
      else if (b.type === 'background') lines.push(`background "${b.params.color || '#090d16'}"`);
      else if (b.type === 'actor') lines.push(`actor ${b.params.name || 'Hero'} [${b.params.x || 120}, ${b.params.y || 240}]`);
      else if (b.type === 'motion') lines.push(`    velocity [${b.params.vx || 8}, 0]`);
      else if (b.type === 'bounce') lines.push(`    bounce ${b.params.val || 0.8}`);
      else if (b.type === 'state') lines.push(`state ${b.params.var || 'val'} = ${b.params.val || 0}`);
      else if (b.type === 'say') lines.push(`say "${b.params.msg || 'Done'}"`);
      else if (b.type === 'on_tick') { lines.push('on tick do'); lines.push('    say "Tick active"'); lines.push('done'); }
      else if (b.type === 'on_key') { lines.push(`on key "${b.params.key || 'Space'}" do`); lines.push(`    say "Key ${b.params.key} hit"`); lines.push('done'); }
    }

    const payloadCode = lines.join('\n');

    // Also update main editor with this code so they stay 100% in sync
    if (this.callbacks.syncToEditor) {
      this.callbacks.syncToEditor(payloadCode);
    }

    try {
      const res = await fetch('/api/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: payloadCode })
      });
      const data = await res.json();

      if (data.success) {
        if (this.callbacks.onRunSuccess) {
          this.callbacks.onRunSuccess(data.output || ["FoxVC Engine Active"]);
        }
      } else {
        this.errBox.innerText = `⚠️ Fault: ${data.error}`;
        this.errBox.style.display = 'block';
      }
    } catch (e) {
      this.errBox.innerText = `⚠️ Bridge error: ${e.message}`;
      this.errBox.style.display = 'block';
    }
  }
}

window.VisualLearningMode = VisualLearningMode;
