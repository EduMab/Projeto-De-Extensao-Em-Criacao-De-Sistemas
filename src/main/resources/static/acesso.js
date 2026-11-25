(() => {
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  const card    = $('#card');
  const forms   = { login: $('#loginForm'), signup: $('#signupForm') };
  // true = quem tem "reduzir movimento" ligado no sistema vê a troca de tela sem animação
  const RESPECT_REDUCED_MOTION = true;
  const reduce  = RESPECT_REDUCED_MOTION ? matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  const T       = { close: 560, hold: 340, open: 560 };   // ms; o "close" casa com --t-panel no CSS
  let mode = 'login';
  let busy = false;

  /* ---------- troca de tela ---------- */
  function setMode(next) {
    mode = next;
    card.dataset.mode = next;
    for (const [name, form] of Object.entries(forms)) {
      const on = name === next;
      form.toggleAttribute('inert', !on);     // inativo: sem foco e sem clique (atributo, funciona em qualquer navegador)
      form.setAttribute('aria-hidden', String(!on));   // e é isto que o CSS usa para esconder
    }
  }

  function clearMessages(form) {
    $$('.field', form).forEach(f => f.classList.remove('has-error'));
    $$('.err', form).forEach(e => (e.textContent = ''));
    $$('input', form).forEach(i => i.setAttribute('aria-invalid', 'false'));
    $('.status', form).textContent = '';
  }

  function announce() {                        // leva o foco ao título sem abrir o teclado no celular
    forms[mode].querySelector('h1').focus({ preventScroll: true });
  }

  function switchTo(next) {
    if (busy || next === mode) return;
    busy = true;
    if (reduce.matches) { setMode(next); clearMessages(forms[next]); busy = false; announce(); return; }

    card.dataset.phase = 'closed';            // 1) painéis deslizam e se encontram na diagonal
    setTimeout(() => {                        // 2) com tudo coberto, troca o formulário
      setMode(next);
      clearMessages(forms[next]);
    }, T.close);
    setTimeout(() => { card.dataset.phase = 'opening'; }, T.close + T.hold);   // 3) painéis abrem
    setTimeout(() => {                        // 4) fim
      card.dataset.phase = 'idle';
      busy = false;
      announce();
    }, T.close + T.hold + T.open);
  }

  $$('[data-go]').forEach(b => b.addEventListener('click', () => switchTo(b.dataset.go)));

  /* ---------- mostrar/ocultar senha ---------- */
  $$('[data-reveal]').forEach(btn => btn.addEventListener('click', () => {
    const input = document.getElementById(btn.dataset.reveal);
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    btn.classList.toggle('on', show);
    btn.setAttribute('aria-pressed', String(show));
    btn.setAttribute('aria-label', show ? 'Ocultar senha' : 'Mostrar senha');
  }));

  /* ---------- validação ---------- */
  const emailOk = v => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim());
  const rules = {
    loginEmail:     el => emailOk(el.value) ? '' : 'Digite um e-mail válido, como nome@dominio.com.',
    loginPassword:  el => el.value ? '' : 'Digite sua senha.',
    signupName:     el => el.value.trim().length >= 2 ? '' : 'Digite seu nome completo.',
    signupEmail:    el => emailOk(el.value) ? '' : 'Digite um e-mail válido, como nome@dominio.com.',
    signupPassword: el => el.value.length >= 6 ? '' : 'Use pelo menos 6 caracteres.',
    signupConfirm:  el => el.value === $('#signupPassword').value ? '' : 'As senhas não coincidem.',
  };

  function showError(el, message) {
    const field = el.closest('.field');
    field.classList.toggle('has-error', !!message);
    document.getElementById(el.id + '-err').textContent = message;
    el.setAttribute('aria-invalid', message ? 'true' : 'false');
  }

  function validate(form) {
    let first = null;
    $$('input', form).forEach(el => {
      const rule = rules[el.id];
      if (!rule) return;
      const message = rule(el);
      showError(el, message);
      if (message && !first) first = el;
    });
    return first;
  }

  // corrige o erro enquanto a pessoa digita
  document.addEventListener('input', e => {
    const el = e.target;
    if (!rules[el.id]) return;
    if (el.closest('.field')?.classList.contains('has-error')) showError(el, rules[el.id](el));
    if (el.id === 'signupPassword' && $('#signupConfirm').closest('.field').classList.contains('has-error')) {
      showError($('#signupConfirm'), rules.signupConfirm($('#signupConfirm')));
    }
    $('.status', el.closest('form')).textContent = '';
  });

  /* ---------- envio ---------- */
  Object.values(forms).forEach(form => {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const invalid = validate(form);
      if (invalid) { invalid.focus(); return; }
      if (form.dataset.submitting === 'true') return;

      const btn = $('.btn-primary', form);
      const label = $('.label', btn);
      const original = label.textContent;
      const isSignup = form === forms.signup;
      const status = $('.status', form);
      const parametros = new URLSearchParams();

      if (isSignup) {
        parametros.append('nome', $('#signupName').value.trim());
        parametros.append('email', $('#signupEmail').value.trim());
        parametros.append('senha', $('#signupPassword').value);
      } else {
        parametros.append('email', $('#loginEmail').value.trim());
        parametros.append('senha', $('#loginPassword').value);
      }

      form.dataset.submitting = 'true';
      $$('[data-go]').forEach(button => { button.disabled = true; });
      btn.disabled = true;
      btn.classList.add('is-loading');
      label.textContent = form.dataset.loading;
      status.textContent = '';

      try {
        const response = await fetch(isSignup ? '/cadastro' : '/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          credentials: 'same-origin',
          body: parametros
        });
        let data;
        try {
          data = await response.json();
        } catch {
          throw new Error('O servidor retornou uma resposta inválida. Tente novamente.');
        }

        if (!response.ok) {
          throw new Error(data.mensagem || data.detail || data.message || 'Não foi possível concluir. Tente novamente.');
        }
        if (!data.sucesso) {
          status.textContent = data.mensagem || (isSignup
            ? 'Não foi possível criar sua conta.'
            : 'E-mail ou senha inválidos.');
          return;
        }

        localStorage.setItem('idEstudante', data.idEstudante);
        localStorage.setItem('nomeEstudante', data.nome);
        window.location.assign('/index.html');
      } catch (error) {
        console.error(error);
        status.textContent = error instanceof TypeError
          ? 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.'
          : error.message || 'Não foi possível concluir. Tente novamente.';
      } finally {
        delete form.dataset.submitting;
        $$('[data-go]').forEach(button => { button.disabled = false; });
        btn.disabled = false;
        btn.classList.remove('is-loading');
        label.textContent = original;
      }
    });
  });

  setMode(card.dataset.mode === 'signup' ? 'signup' : 'login');
})();
