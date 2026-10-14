// Trustmarkt article editor helpers (app.trustmarkt.de/artikel/<id>).
// Paste this whole file as the `text` of one javascript_tool call (returns 'tm helpers ready'),
// then call the functions one per javascript_tool call, e.g.  await __tm.guard()
// Keep every call under ~25 s: the tool times out at 45 s and a frozen renderer is a pain.
// Editor = Editor.js blocks + Pintura image editor, inside a Livewire page.
(() => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const blocks = () => [...document.querySelectorAll('.ce-block')];
  const isH2 = b => !!b.querySelector('.ce-header');
  const h2Index = text => blocks().findIndex(b => isH2(b) && norm(b.textContent) === norm(text));
  const btn = label => [...document.querySelectorAll('button')].filter(b => norm(b.textContent) === label);

  window.__tm = {
    // Step 0 - ALWAYS first. Chrome auto-translate rewrites the editor DOM; saving then stores English.
    guard() {
      const cls = document.documentElement.className;
      const lang = document.documentElement.lang;
      return { ok: lang === 'de' && !/translated/.test(cls), lang, htmlClass: cls, url: location.href };
    },

    // Captures the temporary <input type=file> the Bild block creates, instead of opening a native
    // dialog. The input gets appended to <body> so find() can give it a ref for file_upload.
    installHook() {
      if (!window.__origClick) window.__origClick = HTMLInputElement.prototype.click;
      window.__captured = null;
      HTMLInputElement.prototype.click = function () {
        if (this.type === 'file' && !this.closest('.field__item')) {   // .field__item = Vorschaubild input
          this.style.cssText = 'position:fixed;left:0;top:0;opacity:0.01;width:1px;height:1px';
          document.body.appendChild(this);
          window.__captured = this;
          return;
        }
        return window.__origClick.apply(this, arguments);
      };
      return 'hook installed';
    },

    summary() {
      return blocks().map((b, i) => b.querySelector('.image-tool')
        ? { i, image: b.querySelector('.image-tool--filled') ? 'filled' : 'EMPTY', caption: norm(b.querySelector('.image-tool__caption').textContent).slice(0, 50) }
        : isH2(b) ? { i, h2: norm(b.textContent) } : null).filter(Boolean);
    },

    // Hover the H2 block, open + , choose Bild. The new image block lands DIRECTLY after the H2.
    // Afterwards: find the hidden file input -> file_upload -> clickFertig().
    async bildAfterH2(h2) {
      const idx = h2Index(h2);
      if (idx < 0) throw new Error('H2 not found: ' + h2);
      const next = blocks()[idx + 1];
      if (next && next.querySelector('.image-tool')) throw new Error('an image block already follows this H2');
      // The first image needs >= 3 blocks before it (2+ intro paragraphs + this H2). idx = blocks before the H2.
      const isFirstImage = !blocks().slice(0, idx).some(b => b.querySelector('.image-tool'));
      if (isFirstImage && idx + 1 < 3) throw new Error(`first image would have only ${idx + 1} block(s) before it (need >= 3): ${h2}`);
      const content = blocks()[idx].querySelector('.ce-block__content');
      const r = content.getBoundingClientRect();
      content.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: r.x + 20, clientY: r.y + r.height / 2 }));
      await sleep(400);
      const plus = document.querySelector('.ce-toolbar__plus');
      const py = plus.getBoundingClientRect().y, b = blocks()[idx].getBoundingClientRect();
      if (py < b.y - 5 || py > b.y + b.height + 5) throw new Error('toolbar is not aligned with the H2 block');
      plus.click(); await sleep(500);
      window.__captured = null;
      const item = [...document.querySelectorAll('.ce-popover--opened .ce-popover-item')].find(i => i.dataset.itemName === 'image');
      if (!item) throw new Error('Bild item not in popover');
      item.click(); await sleep(600);
      return { idx, captured: !!window.__captured };
    },

    // Pintura crop editor ("Bild wird verarbeitet..." can take 10 s to 4 min). Click once, then poll filled().
    clickFertig() {
      const l = [...document.querySelectorAll('.PinturaButtonLabel')].find(e => norm(e.textContent) === 'Fertig');
      if (!l) return { clicked: false };
      (l.closest('button') || l).click();
      return { clicked: true };
    },
    // Per-image state from the block classes (the Pintura "verarbeitet" text is always in the DOM, so it is NOT a busy signal).
    // uploading = waiting for the crop editor result; filled = image stored on S3 and shown.
    filled() { return { filled: document.querySelectorAll('.image-tool--filled').length, uploading: document.querySelectorAll('.image-tool--uploading').length,
                        total: document.querySelectorAll('.image-tool').length }; },

    // The Editor.js sanitizer strips <strong> (and no bold tool exists in this editor) when saving, so every
    // **bold** passage written via the API would silently lose its bold. <b> survives. Run right before saveDraft().
    preserveFormatting() {
      let strong = 0, em = 0;
      document.querySelectorAll('.ce-block strong').forEach(s => { const b = document.createElement('b'); b.innerHTML = s.innerHTML; s.replaceWith(b); strong++; });
      document.querySelectorAll('.ce-block em').forEach(s => { const i = document.createElement('i'); i.innerHTML = s.innerHTML; s.replaceWith(i); em++; });
      document.querySelectorAll('.ce-block b, .ce-block i').forEach(n => { const h = n.closest('[contenteditable=true]'); h && h.dispatchEvent(new InputEvent('input', { bubbles: true })); });
      return { strongToB: strong, emToI: em };
    },

    // Caption of the image block directly after the H2. Editor caption becomes BOTH figcaption and alt.
    async captionAfterH2(h2, text) {
      const idx = h2Index(h2);
      const b = blocks()[idx + 1];
      if (!b || !b.querySelector('.image-tool--filled')) throw new Error('no filled image directly after ' + h2);
      const cap = b.querySelector('.image-tool__caption');
      cap.focus(); document.execCommand('selectAll', false, null); document.execCommand('insertText', false, text);
      await sleep(300);
      return { ok: cap.textContent === text };
    },

    // Vorschaubild caption field (plain input, max 90 chars - the editor refuses to save longer ones).
    async coverCaption(text) {
      if (text.length > 90) throw new Error('cover caption is ' + text.length + ' chars, max 90');
      const el = [...document.querySelectorAll('input')].find(e => (e.placeholder || '').startsWith('Bildunterschrift') && !e.closest('.ce-block'));
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, text);
      el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true }));
      await sleep(500);
      return { ok: el.value === text };
    },

    // Category / author dropdowns: options (.bc-option) exist in the DOM even while closed; clicking one selects it.
    async pick(name) {
      const o = [...document.querySelectorAll('.bc-option')].filter(x => norm(x.textContent) === name);
      if (o.length !== 1) throw new Error(`expected exactly 1 option "${name}", found ${o.length}`);
      o[0].click(); await sleep(700);
      return { picked: name };
    },

    saveDraft() { const b = btn('Entwurf sichern')[0]; b.click(); return 'save clicked'; },
    validationErrors() { return [...document.querySelectorAll('[class*=error], .text-red-500')].map(e => norm(e.innerText)).filter(Boolean); },
  };
  return 'tm helpers ready';
})();
