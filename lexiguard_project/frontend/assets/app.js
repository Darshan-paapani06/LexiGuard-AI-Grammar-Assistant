(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const editor = $('editor');
  let suggestions = [];
  let lastCheckedText = '';
  let timer = null;
  const examples = {
    email: 'dear Hiring Manager,\n\ni am writing to express my interest in teh position. I have recieved your email and i am very very excited about this opportunity. I believe an good communication skill is important for this role.\n\nThank you for your time and consideration',
    essay: 'artificial intelligence is changing the way students learn. It give opportunities to practice a new skills. However, students shouldnt depend on technology for every answer. There are many benifits to using AI in education',
    casual: 'hi! i hope your doing well. I dont have much time today but i wanted to share a idea with you. This is are something we can discuss later!!'
  };
  function notify(message) {
    const t = $('toast'); t.textContent = message; t.classList.add('show');
    clearTimeout(timer); timer = setTimeout(() => t.classList.remove('show'), 3600);
  }
  async function api(path, options = {}) {
    let response;
    try { response = await fetch(path, {headers: {'Content-Type':'application/json'}, ...options}); }
    catch (e) { throw new Error('Cannot reach the local server. Check that it is running.'); }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
    return data;
  }
  function updateCounts() {
    const text = editor.value;
    const words = (text.match(/\b[\w']+\b/g) || []).length;
    $('wordCount').textContent = words;
    $('charCount').textContent = text.length;
    $('readTime').textContent = (words / 220).toFixed(1).replace(/\.0$/, '') + ' min read';
    if (text !== lastCheckedText) {
      $('engineBadge').textContent = 'EDITED';
      $('applyAllBtn').disabled = true;
      if (suggestions.length) {
        $('suggestions').innerHTML = '<div class="empty-state"><h4>Text has changed</h4><p>Run another check to refresh the suggestions for your latest draft.</p></div>';
        $('suggestionTotal').textContent = '—';
      }
    }
  }
  function textEl(tag, className, value) {
    const el = document.createElement(tag); if (className) el.className = className;
    el.textContent = value; return el;
  }
  function renderSuggestions(items) {
    const parent = $('suggestions'); parent.replaceChildren();
    if (!items.length) {
      parent.innerHTML = '<div class="empty-state"><div class="empty-image">✧<span>✦</span></div><h4>Looking sharp!</h4><p>No issues found by this checker. You can still review your writing manually.</p></div>';
      return;
    }
    items.forEach((item, i) => {
      const card = textEl('div', 'issue', '');
      const top = textEl('div', 'issue-top', '');
      top.append(textEl('span', 'issue-category ' + item.category, item.category));
      const button = textEl('button', '', 'Apply fix ↗');
      button.addEventListener('click', () => applyOne(i)); top.append(button);
      card.append(top, textEl('p', '', item.message));
      const diff = textEl('div', 'issue-diff', '');
      diff.append(textEl('del', '', item.original || '∅'), textEl('span', '', '→'), textEl('ins', '', item.replacement || '∅'));
      card.append(diff); parent.append(card);
    });
  }
  function replaceInText(text, s) {
    return text.slice(0, s.start) + s.replacement + text.slice(s.end);
  }
  async function doCheck() {
    const text = editor.value;
    if (!text.trim()) {notify('Write a few words first.'); editor.focus(); return;}
    const btn = $('checkBtn'); btn.disabled = true; btn.textContent = 'Checking…';
    try {
      const data = await api('/api/analyze', {method:'POST', body: JSON.stringify({text, engine:$('engineSelect').value})});
      if (text !== editor.value) {notify('Document changed during analysis. Run the check again.'); return;}
      lastCheckedText = text; suggestions = data.suggestions;
      $('scoreValue').textContent = data.metrics.score;
      $('scoreRing').style.setProperty('--score', data.metrics.score);
      $('scoreText').textContent = suggestions.length ? `${suggestions.length} opportunities to improve your writing.` : 'Your writing looks great! Keep it up.';
      $('issueCount').textContent = suggestions.length;
      $('sentenceCount').textContent = data.metrics.sentences;
      $('avgWords').textContent = data.metrics.avg_sentence_words;
      $('suggestionTotal').textContent = suggestions.length;
      $('applyAllBtn').disabled = !suggestions.length;
      $('engineBadge').textContent = 'ANALYZED';
      renderSuggestions(suggestions);
      notify(suggestions.length ? `Found ${suggestions.length} suggestions.` : 'No issues detected by this checker.');
    } catch (e) {notify(e.message);} finally {btn.disabled = false; btn.innerHTML = '<span>✦</span> Check writing <span class="arrow">↗</span>';}
  }
  function applyOne(index) {
    if (editor.value !== lastCheckedText) {notify('Run a fresh check before applying suggestions.'); return;}
    const s = suggestions[index]; if (!s) return;
    editor.value = replaceInText(editor.value, s);
    const change = s.replacement.length - (s.end - s.start);
    suggestions = suggestions.filter((_, i) => i !== index).map(x => {
      if (x.start >= s.end) return {...x, start:x.start + change, end:x.end + change};
      return x;
    });
    lastCheckedText = editor.value;
    $('issueCount').textContent = suggestions.length;
    $('suggestionTotal').textContent = suggestions.length;
    $('applyAllBtn').disabled = !suggestions.length;
    renderSuggestions(suggestions); updateCounts(); notify('Suggestion applied.');
  }
  function applyAll() {
    if (editor.value !== lastCheckedText) {notify('Run a fresh check before applying suggestions.');return;}
    for (const s of [...suggestions].sort((a,b) => b.start-a.start)) editor.value = replaceInText(editor.value,s);
    suggestions = []; lastCheckedText = editor.value;
    $('issueCount').textContent = '0'; $('suggestionTotal').textContent = '0';
    $('applyAllBtn').disabled = true; renderSuggestions([]); updateCounts(); notify('All suggestions applied.');
  }
  function modal(contentFn) {
    $('modalBackdrop').hidden = false; $('modalContent').replaceChildren(); contentFn($('modalContent'));
  }
  function closeModal() { $('modalBackdrop').hidden = true; }
  function el(tag, attrs={}, value='') {
    const node = document.createElement(tag);
    for (const [key,val] of Object.entries(attrs)) node.setAttribute(key,val);
    if (value) node.textContent = value;
    return node;
  }
  function modalButton(text, onClick) {const b = el('button', {class:'btn-primary modal-btn', type:'button'}, text);b.addEventListener('click',onClick); return b;}
  function openSave() {
    if (!editor.value.trim()) {notify('Write something before saving a draft.'); return;}
    modal(root => {
      root.append(el('label',{for:'draft-title'},'Draft title'));
      const title = el('input',{id:'draft-title',maxlength:'120',placeholder:'My brilliant draft'});
      root.append(title,el('label',{for:'draft-pass'},'Encryption passphrase (8+ characters)'));
      const pass = el('input',{id:'draft-pass',type:'password',autocomplete:'new-password',placeholder:'Enter a strong private passphrase'});
      root.append(pass,el('div',{class:'modal-note'},'🔒 Your title and text are encrypted on your server using AES-256-GCM. Your passphrase is not stored or recoverable. This local vault is not a substitute for user accounts or production-grade access controls.'));
      root.append(modalButton('Encrypt & save draft', async () => {
        if (!title.value.trim() || pass.value.length < 8) {notify('Add a title and a passphrase of at least 8 characters.'); return;}
        try {await api('/api/vault',{method:'POST',body:JSON.stringify({title:title.value,content:editor.value,passphrase:pass.value})});pass.value='';closeModal();notify('Draft encrypted and saved. Keep your passphrase safe!');}
        catch(e){notify(e.message);}
      }));
    });
  }
  async function openVault() {
    modal(root => root.append(el('p',{class:'modal-note'},'Loading encrypted drafts…')));
    try {
      const {drafts} = await api('/api/vault');
      const root = $('modalContent'); root.replaceChildren();
      root.append(el('div',{class:'modal-note'},'Titles and text are encrypted. Only random draft IDs and creation times are visible before unlocking.'));
      if (!drafts.length) {root.append(el('p',{},'No saved drafts yet. Select “Encrypt & save” from the editor to create one.'));return;}
      drafts.forEach((draft,i) => {
        const row = el('div',{class:'vault-row'}), info=el('div');
        info.append(el('strong',{},`Encrypted draft #${i+1}`),el('small',{},new Date(draft.created_at).toLocaleString()));
        const actions=el('div'), unlock=el('button',{},'Unlock'), remove=el('button',{},'Delete');
        unlock.addEventListener('click',()=>openUnlock(draft.id));
        remove.addEventListener('click',async()=>{
          if(!confirm('Permanently delete this encrypted draft?'))return;
          try{await api(`/api/vault/${encodeURIComponent(draft.id)}`,{method:'DELETE'});notify('Draft deleted.');openVault();}catch(e){notify(e.message);}
        });
        actions.append(unlock,remove);row.append(info,actions);root.append(row);
      });
    } catch (e) {notify(e.message);closeModal();}
  }
  function openUnlock(id) {
    modal(root => {
      root.append(el('label',{for:'unlock-pass'},'Enter your draft passphrase'));
      const pass=el('input',{id:'unlock-pass',type:'password',autocomplete:'off',placeholder:'Passphrase'});
      root.append(pass,el('div',{class:'modal-note'},'Your passphrase derives an encryption key locally on the server. Wrong passwords cannot decrypt the document.'));
      root.append(modalButton('Decrypt & open in editor',async()=>{
        try {
          const draft=await api(`/api/vault/${encodeURIComponent(id)}/unlock`,{method:'POST',body:JSON.stringify({passphrase:pass.value})});
          if(editor.value.trim()&&!confirm('Opening will replace the current editor text. Continue?'))return;
          editor.value=draft.content; pass.value=''; closeModal(); suggestions=[];lastCheckedText='';updateCounts();
          $('scoreValue').textContent='—';$('scoreRing').style.setProperty('--score',0);$('scoreText').textContent='Run a check to analyze the opened draft.';
          $('issueCount').textContent='0';$('suggestionTotal').textContent='0';$('applyAllBtn').disabled=true;renderSuggestions([]);
          notify(`Opened: ${draft.title}`);
        }catch(e){notify(e.message);}
      }));
    });
  }
  function showRewrite(text) {
    modal(root => {
      root.append(el('div',{class:'modal-note'},'The local transformer proposes a complete rewrite. Please review wording and meaning before replacing your draft.'));
      const pre=el('div',{style:'padding:14px;border:1px solid #e8e9f6;border-radius:9px;white-space:pre-wrap;line-height:1.8;max-height:45vh;overflow:auto'},text);
      root.append(pre,modalButton('Replace editor with this version',()=>{editor.value=text;lastCheckedText='';suggestions=[];closeModal();updateCounts();notify('AI rewrite inserted into editor.');}));
    });
  }
  async function doRewrite() {
    if(!editor.value.trim()){notify('Enter text before requesting an AI rewrite.');return;}
    const btn=$('rewriteBtn');btn.disabled=true;btn.textContent='Loading model…';
    try{const data=await api('/api/rewrite',{method:'POST',body:JSON.stringify({text:editor.value})});showRewrite(data.rewritten);}
    catch(e){notify(e.message);}finally{btn.disabled=false;btn.innerHTML='<span>✧</span> Rewrite with AI';}
  }
  editor.addEventListener('input',updateCounts);
  $('checkBtn').addEventListener('click',doCheck);
  $('applyAllBtn').addEventListener('click',applyAll);
  $('saveBtn').addEventListener('click',openSave);
  $('nav-vault').addEventListener('click',openVault);
  $('nav-editor').addEventListener('click',()=>editor.focus());
  $('clearBtn').addEventListener('click',()=>{if(editor.value&&!confirm('Clear the current document?'))return;editor.value='';lastCheckedText='';suggestions=[];updateCounts();$('scoreValue').textContent='—';$('scoreRing').style.setProperty('--score',0);$('scoreText').textContent='Your writing score will appear here.';$('issueCount').textContent='0';$('suggestionTotal').textContent='0';$('applyAllBtn').disabled=true;renderSuggestions([]);editor.focus();});
  $('copyBtn').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(editor.value);notify('Text copied to clipboard.');}catch(e){editor.select();notify('Select and copy text using Ctrl+C.');}});
  $('rewriteBtn').addEventListener('click',doRewrite);
  $('closeModal').addEventListener('click',closeModal);
  $('modalBackdrop').addEventListener('click',e=>{if(e.target===$('modalBackdrop'))closeModal();});
  $('theme').addEventListener('click',()=>{document.body.classList.toggle('dark');$('theme').textContent=document.body.classList.contains('dark')?'☀':'☾';});
  document.querySelectorAll('[data-example]').forEach(btn=>btn.addEventListener('click',()=>{if(editor.value.trim()&&!confirm('Replace your current document with an example?'))return;editor.value=examples[btn.dataset.example];lastCheckedText='';suggestions=[];updateCounts();editor.focus();notify('Example loaded. Click “Check writing” to analyze it.');}));
  document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();doCheck();}if(e.key==='Escape')closeModal();});
  updateCounts();
})();
