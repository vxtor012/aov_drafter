(function () {
    'use strict';
    const data = window.ATTACK_SPEED_DATA;
    const $ = id => document.getElementById(id);
    const models = Object.keys(data.models);
    const heroes = [...data.heroes].sort((a, b) => a.name.localeCompare(b.name, 'vi'));
    const byId = new Map(heroes.map(hero => [hero.id, hero]));
    const sources = new Map(data.sources.map(source => [source.id, source]));
    const format = value => value.toLocaleString('vi-VN', { maximumFractionDigits: 2 });
    const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLowerCase();
    const date = value => value ? value.split('-').reverse().join('/') : 'Không ghi ngày';
    let hero, formIndex = 0;

    function node(tag, text, className) {
        const element = document.createElement(tag);
        if (text !== undefined) element.textContent = text;
        if (className) element.className = className;
        return element;
    }
    function sourceLink(source) {
        const link = node('a', source.title);
        link.href = source.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        return link;
    }
    function label(form) {
        if (form.status === 'partial') return `Model ${form.model} · chưa đủ mốc`;
        if (form.model) return `Model ${form.model}`;
        if (form.status === 'none') return 'Cơ chế riêng';
        if (form.status === 'special') return form.reference_model ? `Gần ${form.reference_model} · có mốc riêng` : 'Ngoại lệ · chưa đủ bảng';
        return 'Chưa có dữ liệu';
    }
    function showPane(name) {
        document.querySelector('.speed-workspace').dataset.pane = name;
        document.querySelectorAll('.speed-mobile-tabs button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.pane === name)));
    }
    function setHero(id, index = 0, fromPicker = false) {
        hero = byId.get(id) || byId.get('valhein') || heroes[0];
        formIndex = Math.min(Math.max(index, 0), hero.forms.length - 1);
        const form = hero.forms[formIndex];
        $('board-form-select').replaceChildren(...hero.forms.map((entry, i) => {
            const option = node('option', entry.label);
            option.value = String(i);
            return option;
        }));
        $('board-form-select').value = String(formIndex);
        $('matrix-avatar').src = hero.avatar;
        $('matrix-hero-name').textContent = hero.name;
        $('matrix-hero-model').textContent = label(form);
        $('hero-note').textContent = hero.note;
        $('hero-note').hidden = !hero.note;
        const evidence = $('hero-evidence');
        evidence.replaceChildren(document.createTextNode('Nguồn: '));
        hero.evidence.forEach((id, index) => {
            if (index) evidence.append(document.createTextNode(' · '));
            evidence.append(sourceLink(sources.get(id)));
        });
        evidence.append(document.createTextNode(`. Rà soát ${date(data.reviewed)}; chưa đo lại trong game VN.`));
        history.replaceState(null, '', `${location.pathname}${location.search}#hero=${hero.id}&form=${formIndex}`);
        renderMatrix();
        // Keep the picker scroll position and focus when highlighting a new hero.
        if (fromPicker) {
            document.querySelectorAll('.speed-hero-card').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.id === hero.id)));
            if (matchMedia('(max-width: 760px)').matches) showPane('frames');
        } else renderDirectory();
    }
    function renderMatrix() {
        const form = hero.forms[formIndex];
        document.querySelectorAll('.breakpoint-matrix thead [data-model]').forEach(cell => cell.classList.toggle('selected-model', cell.dataset.model === form.model));
        const rows = [];
        for (let frames = 25; frames >= 6; frames--) {
            const row = node('tr');
            const heading = node('th', String(frames));
            heading.scope = 'row';
            row.append(heading);
            for (const model of models) {
                const entry = data.models[model].rows.find(entry => entry.frames === frames);
                const cell = node('td', entry ? `${format(entry.percent)}%` : '—', entry ? '' : 'empty-cell');
                cell.dataset.model = model;
                cell.dataset.frames = String(frames);
                if (model === form.model) cell.classList.add('selected-model');
                if (entry) {
                    const provenance = entry.sources.map(id => sources.get(id).title).join('; ');
                    cell.title = `${model}: ${format(entry.percent)}% / ${frames} frame. ${provenance}`;
                }
                row.append(cell);
            }
            rows.push(row);
        }
        $('matrix-body').replaceChildren(...rows);
    }
    function renderDirectory() {
        const query = normalize($('directory-search').value.trim());
        const filter = $('directory-filter').value;
        const shown = heroes.filter(entry => normalize(entry.name).includes(query) && (filter === 'all' || entry.forms.some(form => form.model === filter || form.status === filter)));
        $('directory-count').textContent = `${shown.length} / ${heroes.length} tướng`;
        $('directory-body').replaceChildren(...shown.map(entry => {
            const button = node('button', undefined, 'speed-hero-card');
            button.type = 'button';
            button.dataset.id = entry.id;
            button.setAttribute('aria-pressed', String(entry.id === hero.id));
            const summary = entry.forms.map(form => `${form.label}: ${label(form)}`).join(' / ');
            button.setAttribute('aria-label', `${entry.name}, ${summary}`);
            button.title = `${entry.name}: ${summary}`;
            const image = node('img');
            image.src = entry.avatar;
            image.alt = '';
            image.loading = 'lazy';
            image.addEventListener('error', () => { image.src = 'assets/img/aov_logo.png'; }, { once: true });
            const badges = [...new Set(entry.forms.map(form => form.model ? `${form.model}${form.status === 'partial' ? '*' : ''}` : form.reference_model ? `${form.reference_model}*` : form.status === 'unknown' ? '?' : 'Riêng'))];
            button.append(image, node('span', entry.name, 'speed-hero-name'), node('span', badges.join('/'), 'speed-hero-model'));
            button.addEventListener('click', () => setHero(entry.id, 0, true));
            return button;
        }));
        $('directory-empty').hidden = shown.length > 0;
    }
    function selectFromHash() {
        const params = new URLSearchParams(location.hash.slice(1));
        const index = Number.parseInt(params.get('form'), 10);
        setHero(params.get('hero'), Number.isFinite(index) ? index : 0);
    }
    $('directory-search').addEventListener('input', renderDirectory);
    $('directory-filter').addEventListener('change', renderDirectory);
    $('board-form-select').addEventListener('change', event => setHero(hero.id, Number(event.target.value)));
    $('matrix-avatar').addEventListener('error', () => { $('matrix-avatar').hidden = true; });
    $('matrix-avatar').addEventListener('load', () => { $('matrix-avatar').hidden = false; });
    document.querySelectorAll('.speed-mobile-tabs button').forEach(button => button.addEventListener('click', () => showPane(button.dataset.pane)));
    window.addEventListener('hashchange', () => { if (new URLSearchParams(location.hash.slice(1)).has('hero')) selectFromHash(); });
    $('review-note').textContent = data.verification_note;
    $('source-list').replaceChildren(...data.sources.map(source => {
        const entry = node('div', undefined, 'source-entry');
        entry.append(sourceLink(source), document.createTextNode(` · ${date(source.date)} · ${source.kind}`), node('p', source.scope));
        return entry;
    }));
    const media = matchMedia('(prefers-color-scheme: dark)');
    let theme = 'dark';
    try { theme = localStorage.getItem('theme') || 'dark'; } catch (_) { /* Keep default when storage is unavailable. */ }
    if (!['light', 'dark', 'system'].includes(theme)) theme = 'dark';
    const applyTheme = () => {
        document.documentElement.dataset.theme = theme === 'system' ? (media.matches ? 'dark' : 'light') : theme;
        document.querySelectorAll('[data-theme-val]').forEach(button => {
            const active = button.dataset.themeVal === theme;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
    };
    document.querySelectorAll('[data-theme-val]').forEach(button => button.addEventListener('click', () => {
        theme = button.dataset.themeVal;
        try { localStorage.setItem('theme', theme); } catch (_) { /* Theme still applies. */ }
        applyTheme();
    }));
    media.addEventListener('change', () => { if (theme === 'system') applyTheme(); });
    applyTheme();
    selectFromHash();
})();
