  /* ============================================================
     KCLC · JS — Midnight Gold (v4 — надёжная трансляция)
     ============================================================ */
  'use strict';
  // ── CONFIG ──────────────────────────────────────────────────────────────────
  const CFG = Object.freeze({
    YT_CHANNEL_ID: 'UCUntqEjTbvNznwBpRN-4wLw',
    YT_CHANNEL_URL: 'https://www.youtube.com/@kclcfamily',
    YT_NS: 'http://www.youtube.com/xml/schemas/2015',
    BCAST_H: 11,     // час начала (Красноярск)
    BCAST_END: 14,     // час окончания (Красноярск, с запасом)
    STREAM_KW: ['ВОСКРЕСНОЕ СЛУЖЕНИЕ'],
    TZ: 'Asia/Krasnoyarsk',
    CAROUSEL_MS: 6500,
    FETCH_TIMEOUT: 7000,
    RSS_URL: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCUntqEjTbvNznwBpRN-4wLw',
    BACKEND_URL: '/api/live-stream/',
    PROXIES: [
      'https://api.allorigins.win/raw?url=',
      'https://corsproxy.io/?url=',
    ],
    RUTUBE_CHANNEL_URL: 'https://rutube.ru/channel/39733690/',
    RUTUBE_BACKEND_URL: '/api/rutube-stream/',
  });
  // ── УТИЛИТЫ ─────────────────────────────────────────────────────────────────
  const $ = id => document.getElementById(id);
  const $$ = s => document.querySelectorAll(s);
  const pad = n => String(n).padStart(2, '0');
  const motionMQ = window.matchMedia('(prefers-reduced-motion: reduce)');
  let REDUCED_MOTION = motionMQ.matches;
  motionMQ.addEventListener('change', e => {
    REDUCED_MOTION = e.matches;
    if (REDUCED_MOTION) stopCarouselAuto(); else startCarouselAuto();
  });
  const scrollSmooth = (el, opts = {}) => {
    if (!el) return;
    const offset = el.getBoundingClientRect().top + window.scrollY - 80;
    window.scrollTo({ top: offset, behavior: REDUCED_MOTION ? 'instant' : (opts.behavior ?? 'smooth') });
  };
  const getKraTime = () => {
    const str = new Date().toLocaleString('en-CA', {
      timeZone: CFG.TZ, hour12: false,
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
    const [Y, M, D, h, m, s] = str.split(/\D+/).map(Number);
    return new Date(Y, M - 1, D, h, m, s);
  };
  const getKraTimeString = () =>
    new Date().toLocaleTimeString('ru-RU', {
      timeZone: CFG.TZ, hour: '2-digit', minute: '2-digit',
    }) + '\u00a0GMT+7';
  // ── УПРАВЛЕНИЕ ИНТЕРВАЛАМИ ───────────────────────────────────────────────────
  const _intervals = new Map();
  const addInterval = (name, fn, ms) => {
    if (_intervals.has(name)) clearInterval(_intervals.get(name));
    _intervals.set(name, setInterval(fn, ms));
  };
  const clearAllIntervals = () => { _intervals.forEach(id => clearInterval(id)); _intervals.clear(); };
  window.addEventListener('beforeunload', clearAllIntervals);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      clearAllIntervals();
    } else {
      updateClock(); updateCountdown(); detectState(); startIntervals();
    }
  });
  // ── ESCAPE ───────────────────────────────────────────────────────────────────
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    const live = $('state-live');
    if (live && !live.classList.contains('state-hidden')) { showTimerState('timer'); return; }
    const presoon = $('state-presoon');
    if (presoon && !presoon.classList.contains('state-hidden')) { showTimerState('timer'); }
  });
  // ── СЕКЦИИ / НАВИГАЦИЯ ───────────────────────────────────────────────────────
  const SECTIONS = ['sec-hero', 'sec-timer', 'sec-video', 'sec-podcast', 'sec-news', 'sec-footer'];
  const getActiveIdx = () => {
    let bestIdx = 0;
    let minDiff = Infinity;
    SECTIONS.forEach((id, idx) => {
      const el = $(id);
      if (!el) return;
      const rect = el.getBoundingClientRect();
      // Выбираем секцию, верхняя граница которой ближе всего к верху экрана (с отступом)
      const diff = Math.abs(rect.top - window.innerHeight / 3);
      if (diff < minDiff) {
        minDiff = diff;
        bestIdx = idx;
      }
    });
    return bestIdx;
  };
  const setDesktopNavActive = targetIdx => {
    $$('.vn-item[data-idx]').forEach(el => {
      const match = Number(el.dataset.idx) === targetIdx;
      el.classList.toggle('active', match);
      el.setAttribute('aria-current', match ? 'true' : 'false');
    });
  };
  const setMobileNavActive = targetIdx => {
    $$('.mn-item[data-idx]').forEach(el => {
      const match = Number(el.dataset.idx) === targetIdx;
      el.classList.toggle('active', match);
      el.setAttribute('aria-current', match ? 'true' : 'false');
    });
  };
  const setNavActive = idx => {
    const capped = Math.min(idx, SECTIONS.length - 2);
    setDesktopNavActive(capped);
    setMobileNavActive(capped);
  };
  const scrollToSection = idx => {
    const sec = $(SECTIONS[idx]);
    if (!sec) return;
    const offset = sec.getBoundingClientRect().top + window.scrollY;
    window.scrollTo({ top: offset, behavior: REDUCED_MOTION ? 'instant' : 'smooth' });
  };
  let _rafPending = false;
  window.addEventListener('scroll', () => {
    if (_rafPending) return;
    _rafPending = true;
    requestAnimationFrame(() => {
      _rafPending = false;
      const idx = getActiveIdx();
      setNavActive(idx);
      const scrollTopBtn = $('scrollTop');
      if (scrollTopBtn) scrollTopBtn.classList.toggle('show', idx > 0);
    });
  }, { passive: true });
  [...$$('.vn-item'), ...$$('.mn-item')].forEach(el => {
    const go = () => scrollToSection(Number(el.dataset.idx));
    el.addEventListener('click', go);
    el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
  });
  $('scrollTop').addEventListener('click', () => scrollToSection(0));
  // ── ЧАСЫ ─────────────────────────────────────────────────────────────────────
  const updateClock = () => { const el = $('current-time'); if (el) el.textContent = getKraTimeString(); };
  // ── СОСТОЯНИЯ ТАЙМЕРА ────────────────────────────────────────────────────────
  const STATE_IDS = { timer: 'state-timer', presoon: 'state-presoon', live: 'state-live' };
  const initialState = () => {
    Object.entries(STATE_IDS).forEach(([, id]) => {
      const el = $(id);
      if (!el) return;
      el.style.removeProperty('display');
      el.classList.add('state-hidden');
      el.setAttribute('aria-hidden', 'true');
    });
    showTimerState('timer');
  };
  const showTimerState = mode => {
    Object.entries(STATE_IDS).forEach(([key, id]) => {
      const el = $(id);
      if (!el) return;
      const hidden = key !== mode;
      el.classList.toggle('state-hidden', hidden);
      el.setAttribute('aria-hidden', hidden ? 'true' : 'false');
    });
    if (mode === 'live') {
      const ann = $('ep-announce');
      if (ann) ann.textContent = 'Идёт прямая трансляция богослужения';
    }
  };
  // ── ОБРАТНЫЙ ОТСЧЁТ ─────────────────────────────────────────────────────────
  const updateCountdown = () => {
    const now = getKraTime();
    const day = now.getDay();
    const hour = now.getHours();
    const isSundayBeforeBcast = day === 0 && hour < CFG.BCAST_H;
    if (isSundayBeforeBcast) {
      const target = new Date(now); target.setHours(CFG.BCAST_H, 0, 0, 0);
      const diff = Math.max(0, target - now);
      const el = $('presoon-count');
      if (el) el.textContent = `${pad(Math.floor(diff / 60000))}:${pad(Math.floor((diff % 60000) / 1000))}`;
    }
    const next = new Date(now);
    if (isSundayBeforeBcast) {
      next.setHours(CFG.BCAST_H, 0, 0, 0);
    } else {
      const daysUntilSun = (7 - day) % 7 || 7;
      next.setDate(now.getDate() + daysUntilSun);
      next.setHours(CFG.BCAST_H, 0, 0, 0);
    }
    const diff = Math.max(0, next - now);
    const setT = (id, v) => { const el = $(id); if (el) el.textContent = v; };
    setT('days', Math.floor(diff / 86400000));
    setT('hours', pad(Math.floor((diff % 86400000) / 3600000)));
    setT('minutes', pad(Math.floor((diff % 3600000) / 60000)));
    setT('seconds', pad(Math.floor((diff % 60000) / 1000)));
  };
  // ── VIDEO ID / IFRAME ────────────────────────────────────────────────────────
  const getVideoId = entry => {
    if (!entry) return '';
    const nsEl = entry.getElementsByTagNameNS(CFG.YT_NS, 'videoId')[0];
    if (nsEl?.textContent?.trim()) return nsEl.textContent.trim();
    const href = entry.querySelector('link[rel="alternate"]')?.getAttribute('href') ?? '';
    const vM = href.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
    if (vM) return vM[1];
    const idM = entry.querySelector('id')?.textContent?.match(/video:([a-zA-Z0-9_-]{11})$/);
    if (idM) return idM[1];
    return '';
  };
  const _buildEmbedFallback = (container, videoId) => {
    container.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'vid-fallback';
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    svg.style.cssText = 'width:40px;height:40px;fill:var(--gold);display:block;opacity:.6';
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M21.8 8s-.2-1.4-.8-2c-.8-.8-1.7-.8-2.1-.9C16.3 5 12 5 12 5s-4.3 0-6.9.1c-.4.1-1.3.1-2.1.9C2.4 6.6 2.2 8 2.2 8S2 9.6 2 11.2v1.5c0 1.6.2 3.2.2 3.2s.2 1.4.8 2c.8.8 1.8.8 2.2.8C6.8 19 12 19 12 19s4.3 0 6.9-.1c.4-.1 1.3-.1 2.1-.9.6-.6.8-2 .8-2s.2-1.6.2-3.2v-1.5C22 9.6 21.8 8 21.8 8zM9.7 14.5V9l5.7 2.8-5.7 2.7z');
    svg.appendChild(path);
    const msg = document.createElement('span');
    msg.textContent = 'Видео недоступно для встраивания';
    const link = document.createElement('a');
    link.href = `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}`;
    link.target = '_blank';
    link.rel = 'noopener';
    link.className = 'yt-btn';
    link.style.marginTop = '8px';
    link.textContent = 'Смотреть на YouTube';
    wrap.append(svg, msg, link);
    container.appendChild(wrap);
  };
  const buildIframe = (container, videoId, autoplay = false) => {
    if (!container || !videoId) return;
    if (!/^[a-zA-Z0-9_-]{1,20}$/.test(videoId)) return;
    const iframe = document.createElement('iframe');
    const origin = encodeURIComponent(window.location.origin);
    let src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?rel=0&modestbranding=1&enablejsapi=1&origin=${origin}`;
    if (autoplay) src += '&autoplay=1&mute=1';
    iframe.setAttribute('src', src);
    iframe.title = 'YouTube видео';
    iframe.loading = 'lazy';
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    iframe.allowFullscreen = true;
    iframe.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;border:none';
    // Обработка ошибок YouTube (101, 150 = embed запрещён) — переключаем на Rutube
    const _onYTMessage = async (e) => {
      if (!e.data || typeof e.data !== 'string') return;
      try {
        const msg = JSON.parse(e.data);
        // YouTube error codes: 2, 5, 100, 101, 150 (=153 alias)
        if (msg?.event === 'onError' || msg?.info?.errorCode) {
          const errCode = msg?.info?.errorCode ?? 0;
          // 101 и 150 = embed запрещён владельцем
          if (errCode === 101 || errCode === 150) {
            console.warn(`[YT] Ошибка ${errCode} — embed запрещён, переключаем на Rutube`);
            window.removeEventListener('message', _onYTMessage);
            // Сбрасываем флаг и чистим плеер
            if (container.id === 'live-player') {
              _liveIframeSet = false;
            }
            container.innerHTML = '';
            // Определяем контекст и пробуем Rutube
            const ctx = container.id === 'live-player' ? 'live' : 'prev';
            const ok = await _tryRutubeFallback(container, null, ctx);
            if (!ok && ctx === 'live') {
              _showLiveFallback();
            }
          }
        }
      } catch (_) { }
    };
    window.addEventListener('message', _onYTMessage);
    // Fallback: если iframe не загрузился за 8 секунд — показываем ссылку
    const _loadTimer = setTimeout(() => {
      if (!iframe.contentWindow) {
        console.warn('[YT] iframe не загрузился, показываем fallback');
        window.removeEventListener('message', _onYTMessage);
        _buildEmbedFallback(container, videoId);
      }
    }, 8000);
    iframe.addEventListener('load', () => clearTimeout(_loadTimer), { once: true });
    container.innerHTML = '';
    container.appendChild(iframe);
  };
  // ── ПОЛУЧЕНИЕ ДАННЫХ (бэкенд) ───────────────────────────────────────────────
  // Кеш ответа бэкенда — один запрос, используем и для live, и для prev
  let _backendCache = null;
  const _fetchBackend = async () => {
    if (_backendCache) return _backendCache;
    try {
      const r = await fetch(CFG.BACKEND_URL, { signal: AbortSignal.timeout(5000) });
      if (r.ok) {
        _backendCache = await r.json();
        return _backendCache;
      }
    } catch (_) { }
    return null;
  };
  // Возвращает данные текущего/ближайшего стрима (первый в списке)
  // Также обновляет кнопки платформ правильными ссылками
  const fetchLiveVideoId = async () => {
    const data = await _fetchBackend();
    if (data?.video_id) {
      console.log('[LIVE] video_id:', data.video_id);
      // Обновляем кнопки платформ
      const ruBtn = $('live-ru-btn');
      const ytBtn = $('live-yt-btn');
      if (ruBtn) {
        ruBtn.href = `https://rutube.ru/video/${encodeURIComponent(data.video_id)}/`;
      }
      if (ytBtn && data.all_streams && data.all_streams[0]) {
        // Для YouTube пробуем найти видео по названию или используем канал
        const firstStream = data.all_streams[0];
        // Если это YouTube видео — даём прямую ссылку, иначе — на канал
        ytBtn.href = `https://www.youtube.com/@${CFG.YT_CHANNEL_HANDLE}/videos`;
      }
      return data.video_id;
    }
    return null;
  };
  // Возвращает данные ПРЕДЫДУЩЕГО служения (второй в списке all_streams)
  // Логика: первый стрим — это предстоящее/текущее (для LIVE)
  //          второй стрим — это последнее прошедшее (для видеоповтора)
  const fetchPrevStream = async () => {
    const data = await _fetchBackend();
    if (!data) return null;
    const streams = data.all_streams || [];
    // Для видеоповтора берём второй элемент — последнее прошедшее воскресное служение
    // Если есть только один стрим — берём его (значит других ещё нет)
    const prev = streams.length >= 2 ? streams[1] : (streams.length === 1 ? null : null);
    if (prev?.video_id) {
      console.log('[PREV] video_id:', prev.video_id, 'title:', prev.title);
      return { vid: prev.video_id, title: prev.title || '' };
    }
    return null;
  };
  // ── RUTUBE FALLBACK ──────────────────────────────────────────────────────────
  let _rutubeCache = null;
  const _fetchRutubeBackend = async () => {
    if (_rutubeCache) return _rutubeCache;
    try {
      const r = await fetch(CFG.RUTUBE_BACKEND_URL, { signal: AbortSignal.timeout(5000) });
      if (r.ok) {
        _rutubeCache = await r.json();
        return _rutubeCache;
      }
    } catch (_) { }
    return null;
  };
  const buildRutubeIframe = (container, videoId, autoplay = false) => {
    if (!container || !videoId) return;
    container.innerHTML = '';
    const iframe = document.createElement('iframe');
    let src = `https://rutube.ru/play/embed/${encodeURIComponent(videoId)}?skinColor=c9a84c`;
    if (autoplay) src += '&autoplay=true';
    iframe.setAttribute('src', src);
    iframe.title = 'Rutube видео';
    iframe.loading = 'lazy';
    iframe.allow = 'autoplay; encrypted-media; fullscreen';
    iframe.allowFullscreen = true;
    iframe.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;border:none';
    container.appendChild(iframe);
  };
  // Пробует загрузить Rutube как fallback, возвращает true если удалось
  const _tryRutubeFallback = async (container, btnEl, context) => {
    const data = await _fetchRutubeBackend();
    if (!data?.video_id) return false;
    const streams = data.all_streams || [];
    let target;
    if (context === 'prev') {
      // Если сейчас идёт трансляция — streams[0] это эфир, берём streams[1] (прошлое воскресенье)
      if (data.is_live && streams.length >= 2) {
        target = streams[1];
      } else {
        target = streams[0] || data;
      }
    } else {
      // Для LIVE берём первый стрим (текущее/предстоящее)
      target = streams[0] || data;
    }
    if (!target?.video_id) return false;
    console.log(`[RUTUBE-${context.toUpperCase()}] video_id:`, target.video_id);
    buildRutubeIframe(container, target.video_id, context === 'live');
    // Обновляем кнопки платформ правильными ссылками
    const ruBtn = context === 'live' ? $('live-ru-btn') : $('prev-ru-btn');
    const ytBtn = context === 'live' ? $('live-yt-btn') : $('prev-yt-btn');
    if (ruBtn) {
      // Ссылка на конкретное видео Rutube
      ruBtn.href = `https://rutube.ru/video/${encodeURIComponent(target.video_id)}/`;
    }
    if (ytBtn) {
      // Ссылка на YouTube канал (так как Rutube — основной, YouTube — запасной)
      ytBtn.href = `https://www.youtube.com/@${CFG.YT_CHANNEL_HANDLE}/videos`;
    }
    return true;
  };
  // ── DETECT STATE ─────────────────────────────────────────────────────────────
  let _liveVideoId = null;   // кешируем video ID чтобы не сбрасывать iframe
  let _liveIframeSet = false;  // флаг: iframe уже вставлен
  const _showLiveFallback = () => {
    const lp = $('live-player');
    if (!lp || lp.querySelector('iframe')) return;
    lp.innerHTML = `
    <div class="vid-fallback">
      <svg viewBox="0 0 24 24" aria-hidden="true" style="width:48px;height:48px;fill:var(--live-red)">
        <path d="M21.8 8s-.2-1.4-.8-2c-.8-.8-1.7-.8-2.1-.9C16.3 5 12 5 12 5s-4.3 0-6.9.1c-.4.1-1.3.1-2.1.9C2.4 6.6 2.2 8 2.2 8S2 9.6 2 11.2v1.5c0 1.6.2 3.2.2 3.2s.2 1.4.8 2c.8.8 1.8.8 2.2.8C6.8 19 12 19 12 19s4.3 0 6.9-.1c.4-.1 1.3-.1 2.1-.9.6-.6.8-2 .8-2s.2-1.6.2-3.2v-1.5C22 9.6 21.8 8 21.8 8zM9.7 14.5V9l5.7 2.8-5.7 2.7z"/>
      </svg>
      <p style="color:var(--gold);font-weight:700;font-size:1.1rem;margin:8px 0 4px">Трансляция идёт сейчас!</p>
      <p style="color:rgba(245,240,232,0.6);font-size:0.9rem;margin-bottom:18px">Загружаем плеер…</p>
      <a href="${CFG.YT_CHANNEL_URL}/live" target="_blank" rel="noopener"
         class="yt-btn" style="text-decoration:none">
        <svg viewBox="0 0 24 24" style="width:16px;height:16px;fill:currentColor">
          <path d="M21.8 8s-.2-1.4-.8-2c-.8-.8-1.7-.8-2.1-.9C16.3 5 12 5 12 5s-4.3 0-6.9.1c-.4.1-1.3.1-2.1.9C2.4 6.6 2.2 8 2.2 8S2 9.6 2 11.2v1.5c0 1.6.2 3.2.2 3.2s.2 1.4.8 2c.8.8 1.8.8 2.2.8C6.8 19 12 19 12 19s4.3 0 6.9-.1c.4-.1 1.3-.1 2.1-.9.6-.6.8-2 .8-2s.2-1.6.2-3.2v-1.5C22 9.6 21.8 8 21.8 8zM9.7 14.5V9l5.7 2.8-5.7 2.7z"/>
        </svg>
        Смотреть на YouTube
      </a>
    </div>`;
  };
  const detectState = async () => {
    const now = getKraTime();
    const day = now.getDay();       // 0 = воскресенье
    const h = now.getHours();
    const m = now.getMinutes();
    const inWindow = day === 0 && h >= CFG.BCAST_H && h < CFG.BCAST_END;
    const isBefore = day === 0 && h < CFG.BCAST_H;
    console.log(`[STATE] день=${day} час=${h}:${pad(m)} окно=${inWindow} до=${isBefore}`);
    if (inWindow) {
      // ── ОКНО ТРАНСЛЯЦИИ: переключаем в LIVE немедленно ──────────────────────
      showTimerState('live');
      // Если iframe уже стоит — не трогаем его
      if (_liveIframeSet) return;
      // Показываем заглушку пока ищем video ID
      _showLiveFallback();
      const lp = $('live-player');
      // Сначала пробуем Rutube (приоритет)
      console.log('[LIVE] Пробуем Rutube (приоритет)…');
      const ruLiveData = await _fetchRutubeBackend();
      const ruLiveStreams = ruLiveData?.all_streams || [];
      const ruLiveTarget = ruLiveStreams[0] || (ruLiveData?.video_id ? ruLiveData : null);
      if (ruLiveTarget?.video_id) {
        buildRutubeIframe(lp, ruLiveTarget.video_id, true);
        _liveVideoId = ruLiveTarget.video_id;
        _liveIframeSet = true;
        // Обновляем заголовок
        const ld = $('live-date');
        if (ld) ld.textContent = ruLiveTarget.title || new Date().toLocaleString('ru-RU', {
          timeZone: CFG.TZ, hour: '2-digit', minute: '2-digit',
          day: 'numeric', month: 'long',
        });
        // Обновляем кнопки платформ
        const ruBtn = $('live-ru-btn');
        if (ruBtn) ruBtn.href = `https://rutube.ru/video/${encodeURIComponent(ruLiveTarget.video_id)}/`;
        return;
      }
      // Rutube не дал video_id, пробуем YouTube (резерв)
      console.log('[LIVE] Rutube не дал video_id, пробуем YouTube (резерв)…');
      const vid = await fetchLiveVideoId();
      if (vid) {
        _liveVideoId = vid;
        _liveIframeSet = true;
        buildIframe(lp, vid, true);
        const ld = $('live-date');
        if (ld) ld.textContent = new Date().toLocaleString('ru-RU', {
          timeZone: CFG.TZ, hour: '2-digit', minute: '2-digit',
          day: 'numeric', month: 'long',
        });
      }
      return;
    }
    // Вышли из окна — сбрасываем флаги чтобы в следующий раз заново загрузилось
    if (_liveIframeSet) {
      _liveIframeSet = false;
      _liveVideoId = null;
      const lp = $('live-player');
      if (lp) lp.innerHTML = '';
    }
    if (isBefore) { showTimerState('presoon'); return; }
    showTimerState('timer');
  };
  // ── LOAD PREV ────────────────────────────────────────────────────────────────
  const _buildPrevFallback = () => {
    const pp = $('prev-player');
    if (!pp) return;
    pp.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'vid-fallback';
    const msg = document.createElement('span');
    msg.textContent = 'Не удалось загрузить запись. Откройте канал напрямую.';
    const ytLink = document.createElement('a');
    ytLink.href = CFG.YT_CHANNEL_URL;
    ytLink.target = '_blank'; ytLink.rel = 'noopener';
    ytLink.className = 'yt-btn'; ytLink.style.marginTop = '8px';
    ytLink.textContent = 'Открыть YouTube';
    const ruLink = document.createElement('a');
    ruLink.href = CFG.RUTUBE_CHANNEL_URL;
    ruLink.target = '_blank'; ruLink.rel = 'noopener';
    ruLink.className = 'yt-btn'; ruLink.style.marginTop = '8px';
    ruLink.textContent = 'Открыть Rutube';
    wrap.append(msg, ytLink, ruLink);
    pp.appendChild(wrap);
    const wb = $('watch-btn');
    if (wb) wb.href = CFG.YT_CHANNEL_URL;
  };
  const loadPrev = async () => {
    const pp = $('prev-player');
    // Сначала пробуем Rutube (приоритет)
    console.log('[PREV] Пробуем Rutube (приоритет)…');
    const ruData = await _fetchRutubeBackend();
    if (ruData) {
      const ruStreams = ruData.all_streams || [];
      // Если сейчас идёт трансляция (is_live=true), то all_streams[0] — текущий эфир.
      // Для записи нужно прошлое воскресенье → берём all_streams[1].
      // Если трансляции нет — all_streams[0] уже является последней записью.
      let ruTarget;
      if (ruData.is_live && ruStreams.length >= 2) {
        ruTarget = ruStreams[1];
        console.log('[PREV] is_live=true, берём streams[1]:', ruTarget?.title);
      } else {
        ruTarget = ruStreams[0] || (ruData.video_id ? ruData : null);
        console.log('[PREV] is_live=false, берём streams[0]:', ruTarget?.title);
      }
      if (ruTarget?.video_id) {
        buildRutubeIframe(pp, ruTarget.video_id, false);
        const pd = $('prev-date');
        if (pd) pd.textContent = ruTarget.title || 'Воскресное служение (Rutube)';
        const ruBtn = $('prev-ru-btn');
        const ytBtn = $('prev-yt-btn');
        if (ruBtn) ruBtn.href = `https://rutube.ru/video/${encodeURIComponent(ruTarget.video_id)}/`;
        if (ytBtn) ytBtn.href = CFG.YT_CHANNEL_URL;
        return;
      }
    }
    // Rutube не дал видео, пробуем YouTube как резервный
    console.log('[PREV] Rutube не дал video_id, пробуем YouTube (резерв)…');
    try {
      const found = await fetchPrevStream();
      if (found?.vid) {
        buildIframe(pp, found.vid, false);
        const pd = $('prev-date');
        if (pd) pd.textContent = found.title || 'Воскресное служение';
        const ruBtn = $('prev-ru-btn');
        const ytBtn = $('prev-yt-btn');
        if (ruBtn) ruBtn.href = CFG.RUTUBE_CHANNEL_URL;
        if (ytBtn) ytBtn.href = CFG.YT_CHANNEL_URL;
        return;
      }
    } catch (err) {
      console.warn('[PREV] YouTube не удался:', err.message);
    }
    // Если ничего не удалось — показываем fallback с кнопками на каналы
    _buildPrevFallback();
  };
  // ── КАРУСЕЛЬ ─────────────────────────────────────────────────────────────────
  let slideIdx = 0;
  const slides = Array.from($$('.car-slide'));
  const dots = Array.from($$('.car-dot'));
  const TOTAL = slides.length;
  const setSlideAttrs = n => {
    slides.forEach((s, i) => {
      const on = i === n;
      s.classList.toggle('active', on);
      s.setAttribute('aria-hidden', on ? 'false' : 'true');
    });
    dots.forEach((d, i) => {
      const on = i === n;
      d.classList.toggle('active', on);
      d.setAttribute('aria-selected', on ? 'true' : 'false');
      d.setAttribute('tabindex', on ? '0' : '-1');
    });
  };
  const showSlide = n => {
    if (!TOTAL) return;
    slideIdx = ((n % TOTAL) + TOTAL) % TOTAL;
    setSlideAttrs(slideIdx);
  };
  setSlideAttrs(0);
  let _autoPlay = null;
  const startCarouselAuto = () => {
    if (REDUCED_MOTION) return;
    stopCarouselAuto();
    _autoPlay = setInterval(() => showSlide(slideIdx + 1), CFG.CAROUSEL_MS);
  };
  const stopCarouselAuto = () => { clearInterval(_autoPlay); _autoPlay = null; };
  startCarouselAuto();
  $$('.car-arrow.prev')[0]?.addEventListener('click', () => { showSlide(slideIdx - 1); startCarouselAuto(); });
  $$('.car-arrow.next')[0]?.addEventListener('click', () => { showSlide(slideIdx + 1); startCarouselAuto(); });
  dots.forEach((d, i) => d.addEventListener('click', () => { showSlide(i); startCarouselAuto(); }));
  const carCont = document.querySelector('.car-cont');
  carCont?.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft') { e.preventDefault(); showSlide(slideIdx - 1); stopCarouselAuto(); }
    if (e.key === 'ArrowRight') { e.preventDefault(); showSlide(slideIdx + 1); stopCarouselAuto(); }
    if (e.key === 'Home') { e.preventDefault(); showSlide(0); stopCarouselAuto(); }
    if (e.key === 'End') { e.preventDefault(); showSlide(TOTAL - 1); stopCarouselAuto(); }
  });
  carCont?.setAttribute('tabindex', '-1');
  carCont?.addEventListener('mouseenter', stopCarouselAuto);
  carCont?.addEventListener('mouseleave', startCarouselAuto);
  let _tx = 0, _ty = 0;
  $('car-wrap')?.addEventListener('touchstart', e => { _tx = e.touches[0].clientX; _ty = e.touches[0].clientY; }, { passive: true });
  $('car-wrap')?.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - _tx;
    const dy = e.changedTouches[0].clientY - _ty;
    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 40) { showSlide(dx < 0 ? slideIdx + 1 : slideIdx - 1); startCarouselAuto(); }
  }, { passive: true });
  // ── ПОДКАСТ ──────────────────────────────────────────────────────────────────
  let _isPlaying = false;
  const playBtn = $('play-btn');
  const setPlayState = playing => {
    _isPlaying = playing;
    if (!playBtn) return;
    playBtn.setAttribute('aria-pressed', playing ? 'true' : 'false');
    const svgPath = playBtn.querySelector('path');
    if (svgPath) {
      svgPath.setAttribute('d', playing
        ? 'M6 19h4V5H6v14zm8-14v14h4V5h-4z'
        : 'M8 5v14l11-7z'
      );
    }
  };
  playBtn?.addEventListener('click', () => { setPlayState(!_isPlaying); });
  $$('.ep-row').forEach(row => {
    const select = () => {
      const t = row.dataset.title ?? '', s = row.dataset.speaker ?? '', d = row.dataset.dur ?? '';
      if (!t) return;
      setPlayState(false);
      const setEl = (id, v) => { const el = $(id); if (el) el.textContent = v; };
      setEl('ep-cur-title', t); setEl('ep-cur-speaker', s); setEl('ep-cur-dur', d);
      $$('.ep-row').forEach(r => { r.classList.remove('ep-row--active'); r.setAttribute('aria-current', 'false'); });
      row.classList.add('ep-row--active'); row.setAttribute('aria-current', 'true');
      const ann = $('ep-announce');
      if (ann) ann.textContent = `Выбран эпизод: ${t}${s ? ', ' + s : ''}`;
      if (playBtn) playBtn.setAttribute('aria-label', `Воспроизвести: ${t}`);
      scrollSmooth($('curr-ep'), { block: 'nearest' });
      setTimeout(() => playBtn?.focus(), REDUCED_MOTION ? 0 : 350);
    };
    row.addEventListener('click', select);
    row.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(); } });
  });
  // ── ДИНАМИЧЕСКИЕ СТИЛИ ───────────────────────────────────────────────────────
  const _runtimeStyles = document.createElement('style');
  _runtimeStyles.id = 'runtime-styles';
  _runtimeStyles.textContent = `
  .ep-row--active { color: var(--navy) !important; font-weight: 600; }
  @media (prefers-reduced-motion: reduce) {
    .car-slide, .car-dot, .car-arrow { transition: none !important; }
  }
`;
  document.head.appendChild(_runtimeStyles);
  // ── ЗАПУСК ИНТЕРВАЛОВ ────────────────────────────────────────────────────────
  const startIntervals = () => {
    clearAllIntervals();
    addInterval('clock', updateClock, 30000);
    addInterval('countdown', updateCountdown, 1000);
    // В окне трансляции — проверяем каждые 15 сек, иначе — каждые 60 сек
    const now = getKraTime();
    const inWindow = now.getDay() === 0 && now.getHours() >= CFG.BCAST_H && now.getHours() < CFG.BCAST_END;
    addInterval('detect', detectState, inWindow ? 15000 : 60000);
  };
  // ── ВЕРТИКАЛЬНАЯ НАВИГАЦИЯ (IntersectionObserver) ────────────────────────────
  const initVerticalNav = () => {
    const vNavItems = document.querySelectorAll('.vn-item');
    const sections = document.querySelectorAll('.snap-sec');
    const snapRoot = document.getElementById('snap-root');
    if (!vNavItems.length || !sections.length || !snapRoot) return;
    // Клик по точкам
    vNavItems.forEach(item => {
      item.addEventListener('click', () => {
        const targetId = item.dataset.target;
        if (targetId) {
          const targetSection = document.getElementById(targetId);
          if (targetSection) scrollSmooth(targetSection);
        }
      });
    });
    // Наблюдатель за секциями
    const observerOptions = {
      root: snapRoot,
      threshold: 0.5
    };
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const targetId = entry.target.id;
          vNavItems.forEach(nav => {
            const isActive = nav.dataset.target === targetId;
            nav.classList.toggle('active', isActive);
            if (isActive) {
              nav.setAttribute('aria-current', 'true');
            } else {
              nav.removeAttribute('aria-current');
            }
          });
        }
      });
    }, observerOptions);
    sections.forEach(sec => observer.observe(sec));
  };
  // ── HERO SLIDER ──────────────────────────────────────────────────────────────
  const initHeroSlider = () => {
    const slideEls = document.querySelectorAll('.hero-slide-bg');
    if (slideEls.length <= 1) return;
    let currentSlide = 0;
    setInterval(() => {
      slideEls[currentSlide].classList.remove('opacity-100', 'scale-[1.02]');
      slideEls[currentSlide].classList.add('opacity-0', 'scale-105');
      currentSlide = (currentSlide + 1) % slideEls.length;
      slideEls[currentSlide].classList.remove('opacity-0', 'scale-105');
      slideEls[currentSlide].classList.add('opacity-100', 'scale-[1.02]');
    }, 6000);
  };
  // ── ИНИЦИАЛИЗАЦИЯ ────────────────────────────────────────────────────────────
  const init = () => {
    initialState();
    updateClock();
    updateCountdown();
    detectState();
    loadPrev();
    startIntervals();
    initVerticalNav();
    initHeroSlider();
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
