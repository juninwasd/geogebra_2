// Front-end logic: plotting, i18n and saving via /save
(function(){
  const LANGS = ['en','pt'];
  let translations = {};

  async function loadTranslations(){
    for(const l of LANGS){
      try{
        const res = await fetch(`/static/js/i18n_${l}.json`);
        translations[l] = await res.json();
      }catch(e){
        translations[l] = {};
      }
    }
  }

  function applyTranslations(lang){
    const dict = translations[lang] || {};
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if(dict[key]) el.textContent = dict[key];
    });
  }

  function setupLangSelect(){
    const sel = document.getElementById('lang');
    sel.innerHTML = LANGS.map(l=>`<option value="${l}">${l.toUpperCase()}</option>`).join('');
    sel.addEventListener('change', e=> applyTranslations(e.target.value));
    // default
    sel.value = 'pt';
    applyTranslations('pt');
  }

  function plotExpression(){
    const expr = document.getElementById('expr').value.trim();
    const xmin = parseFloat(document.getElementById('xmin').value)|| -10;
    const xmax = parseFloat(document.getElementById('xmax').value)|| 10;
    const samples = parseInt(document.getElementById('samples').value) || 400;
    const xs = [];
    const ys = [];
    for(let i=0;i<samples;i++){
      const x = xmin + (xmax - xmin) * i / (samples-1);
      xs.push(x);
      try{
        // use math.js to evaluate safely
        const scope = {x: x};
        const y = math.evaluate(expr, scope);
        ys.push(Number(y));
      }catch(e){
        ys.push(NaN);
      }
    }
    const data = [{ x: xs, y: ys, mode: 'lines', line: {width:2} }];
    const layout = {autosize:true, margin:{l:40,r:20,t:20,b:40}, xaxis:{title:'x'}, yaxis:{title:'y'}, dragmode:'pan'};
    const config = { responsive:true, scrollZoom:true }; // scrollZoom enables unlimited zoom with mouse wheel
    Plotly.newPlot('plot', data, layout, config);
  }

  async function savePlot(){
    const expr = document.getElementById('expr').value.trim();
    if(!expr) return alert('Expression required');
    // export plot as png dataurl
    try{
      const dataUrl = await Plotly.toImage(document.getElementById('plot'), {format:'png', width:800, height:600});
      const res = await axios.post('/save',{expr: expr, image: dataUrl});
      if(res.data && res.data.ok){
        alert('Saved');
        loadSaved();
      }else{
        alert('Save failed');
      }
    }catch(e){
      console.error(e);
      alert('Save error');
    }
  }

  async function loadSaved(){
    try{
      const res = await fetch('/api/list');
      const list = await res.json();
      const ul = document.getElementById('savedList');
      ul.innerHTML = '';
      for(const it of list){
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.textContent = `${it.id}: ${it.expr} (${it.created_at})`;
        ul.appendChild(li);
      }
    }catch(e){
      // ignore
    }
  }

  // Authentication UI
  async function loadCurrentUser(){
    try{
      const res = await fetch('/api/current_user');
      const u = await res.json();
      if(u && u.username){
        document.getElementById('notLogged').style.display = 'none';
        document.getElementById('logged').style.display = 'block';
        document.getElementById('currentUser').textContent = u.username;
      }else{
        document.getElementById('notLogged').style.display = 'block';
        document.getElementById('logged').style.display = 'none';
      }
    }catch(e){
      // ignore
    }
  }

  async function doRegister(){
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    if(!username || !password) return alert('username/password required');
    const res = await fetch('/api/register',{method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({username,password})});
    const j = await res.json();
    if(j.ok) { alert('registered'); }
    else alert('register failed');
  }

  async function doLogin(){
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    if(!username || !password) return alert('username/password required');
    const res = await fetch('/api/login',{method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({username,password})});
    const j = await res.json();
    if(j.ok){ loadCurrentUser(); loadSaved(); alert('logged in'); }
    else alert('login failed');
  }

  async function doLogout(){
    await fetch('/api/logout',{method:'POST'});
    loadCurrentUser();
    loadSaved();
  }

  // Virtual keyboard shortcuts
  const SHORTCUTS = [
    'sin(', 'cos(', 'tan(', 'sqrt(', 'log(', 'exp(', 'pi', 'e',
    '^2', '^3', '^(', '(', ')', '/', '*', '-', '+', ' ^ '
  ];

  function insertAtCursor(input, text){
    // for input element
    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const val = input.value;
    const newVal = val.substring(0, start) + text + val.substring(end);
    input.value = newVal;
    // place cursor after inserted text
    const pos = start + text.length;
    input.setSelectionRange(pos, pos);
    input.focus();
  }

  function renderVirtualKb(){
    const row = document.getElementById('kb-row');
    if(!row) return;
    row.innerHTML = '';
    for(const s of SHORTCUTS){
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'kb-btn';
      b.textContent = s;
      b.addEventListener('click', ()=>{
        const inp = document.getElementById('expr');
        insertAtCursor(inp, s);
      });
      row.appendChild(b);
    }
  }

  document.addEventListener('DOMContentLoaded', async ()=>{
    await loadTranslations();
    setupLangSelect();
    document.getElementById('btnPlot').addEventListener('click', plotExpression);
    document.getElementById('btnSave').addEventListener('click', savePlot);
    document.getElementById('btnLogin').addEventListener('click', doLogin);
    document.getElementById('btnRegister').addEventListener('click', doRegister);
    document.getElementById('btnLogout').addEventListener('click', doLogout);
    plotExpression();
    await loadCurrentUser();
    await loadSaved();
    renderVirtualKb();
  });

})();
