/* ============================================================
   KCLC · JS — Midnight Gold (v6 — timezone-safe, clean)
   ============================================================ */
'use strict';

// ── CONFIG ──────────────────────────────────────────────────────────────────
const CFG = Object.freeze({
  YT_CHANNEL_ID: 'UCUntqEjTbvNznwBpRN-4wLw',
  YT_CHANNEL_URL: 'https://www.youtube.com/@kclcfamily',
  YT_NS: 'http://www.youtube.com/xml/schemas/2015',
  BCAST_H: 11,
  BCAST_END: 14,
  STREAM_KW: ['ВОСКРЕСНОЕ СЛУЖЕНИЕ'],
  TZ: 'Asia/Krasnoyarsk',
  KRA_OFFSET: 7,
  FETCH_TIMEOUT: 7000,
  BACKEND_URL: '/api/live-stream/',
  RUTUBE_CHANNEL_URL: 'https://rutube.ru/channel/39733690/',
  RUTUBE_BACKEND_URL: '/api/rutube-stream/',
});

// ── УТИЛИТЫ ─────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const $$ = s => document.querySelectorAll(s);
const pad = n => String(n).padStart(2, '0');

const motionMQ = window.matchMedia('(prefers-reduced-motion: reduce)');
let REDUCED_MOTION = motionMQ.matches;
motionMQ.addEventListener('change', e => { REDUCED_MOTION = e.matches; });

// ── TIMEZONE-SAFE TIME ──────────────────────────────────────────────────────
let _realTimeOffset = 0;
if (window.SERVER_NOW_MS) {
  _realTimeOffset = window.SERVER_NOW_MS - Date.now();
  console.log('[TIMER] Server time offset:', _realTimeOffset, 'ms');
  console.log('[TIMER] Server time:', new Date(window.SERVER_NOW_MS).toISOString());
  console.log('[TIMER] Client time:', new Date().toISOString());
} else {
  console.warn('[TIMER] SERVER_NOW_MS not provided - using client time!');
}

/**
 * Возвращает компоненты текущего красноярского времени (UTC+7).
 * Строго привязано к серверному (т.е. реальному) времени.
 */
const getKraComponents = () => {
  const nowMs = Date.now() + _realTimeOffset;
  const dateUTC = new Date(nowMs);

  // Получаем компоненты в UTC
  let year = dateUTC.getUTCFullYear();
  let month = dateUTC.getUTCMonth();  // 0-11
  let day = dateUTC.getUTCDate();
  let hours = dateUTC.getUTCHours();
  let minutes = dateUTC.getUTCMinutes();
  let seconds = dateUTC.getUTCSeconds();
  let dayOfWeek = dateUTC.getUTCDay();  // 0=Sunday

  // Добавляем смещение Красноярска (+7 часов)
  hours += CFG.KRA_OFFSET;

  // Обрабатываем переход дней
  while (hours >= 24) {
    hours -= 24;
    day += 1;
  }
  while (hours < 0) {
    hours += 24;
    day -= 1;
  }

  // Обрабатываем переход месяцев
  const daysInMonth = (m, y) => [31, (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0 ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m];
  while (day > daysInMonth(month, year)) {
    day -= daysInMonth(month, year);
    month += 1;
  }
  while (day < 1) {
    month -= 1;
    if (month < 0) {
      month = 11;
      year -= 1;
    }
    day += daysInMonth(month, year);
  }

  // Обновляем dayOfWeek для нового дня (если он изменился)
  if (hours !== dateUTC.getUTCHours() || day !== dateUTC.getUTCDate()) {
    const tempDate = new Date(Date.UTC(year, month, day, 12, 0, 0));
    dayOfWeek = tempDate.getUTCDay();
  }

  return {
    year, month, day, hours, minutes, seconds, dayOfWeek
  };
};

/**
 * Конвертирует дату/время Красноярска в UTC-метку (ms).
 */
const kraToUTC = (y, m, d, h, mi = 0, s = 0) =>
  Date.UTC(y, m, d, h, mi, s) - (CFG.KRA_OFFSET * 3600000);

const getKraTimeString = () =>
  new Date(Date.now() + _realTimeOffset).toLocaleTimeString('ru-RU', {
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
const SECTIONS = ['sec-hero', 'sec-events', 'sec-timer', 'sec-podcast', 'sec-news', 'sec-footer'];

const scrollToSection = idx => {
  const sec = $(SECTIONS[idx]);
  if (!sec) return;
  const snapRoot = $('snap-root');
  if (snapRoot) {
    sec.scrollIntoView({ behavior: REDUCED_MOTION ? 'instant' : 'smooth' });
  }
};

// ── Вертикальная навигация ──────────────────────────────────────────────────
const initNav = () => {
  // Клик по элементам v-nav
  $$('.vn-item').forEach(el => {
    const target = el.dataset.target;
    if (!target) return;
    const idx = SECTIONS.indexOf(target);
    if (idx < 0) return;
    const go = () => scrollToSection(idx);
    el.addEventListener('click', go);
    el.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
    });
  });

  // Scroll-top button
  $('scrollTop')?.addEventListener('click', () => scrollToSection(0));

  // IntersectionObserver для отслеживания активной секции
  const snapRoot = $('snap-root');
  if (!snapRoot) return;

  const vNavItems = $$('.vn-item');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const targetId = entry.target.id;
        const idx = SECTIONS.indexOf(targetId);

        // Обновляем v-nav
        vNavItems.forEach(nav => {
          const isActive = nav.dataset.target === targetId;
          nav.classList.toggle('active', isActive);
        });

        // Scroll-top button
        const scrollTopBtn = $('scrollTop');
        if (scrollTopBtn) scrollTopBtn.classList.toggle('show', idx > 0);
      }
    });
  }, { root: snapRoot, threshold: 0.5 });

  $$('.snap-sec').forEach(sec => observer.observe(sec));
};

// ── ЧАСЫ ─────────────────────────────────────────────────────────────────────
const updateClock = () => { const el = $('current-time'); if (el) el.textContent = getKraTimeString(); };

// ── СОСТОЯНИЯ ТАЙМЕРА ────────────────────────────────────────────────────────
const STATE_IDS = { timer: 'state-timer', live: 'state-live' };

const showTimerState = mode => {
  Object.entries(STATE_IDS).forEach(([key, id]) => {
    const el = $(id);
    if (!el) return;
    const hidden = key !== mode;
    el.classList.toggle('state-hidden', hidden);
    el.setAttribute('aria-hidden', hidden ? 'true' : 'false');
  });
};

// ── ОБРАТНЫЙ ОТСЧЁТ ─────────────────────────────────────────────────────────
const updateCountdown = () => {
  const kra = getKraComponents();
  const nowUTC = Date.now() + _realTimeOffset;
  const day = kra.dayOfWeek;
  const hour = kra.hours;

  const isSundayBeforeBcast = day === 0 && hour < CFG.BCAST_H;
  const isSundayLive = day === 0 && hour >= CFG.BCAST_H && hour < CFG.BCAST_END;

  // Отладка каждую минуту
  if (kra.minutes % 10 === 0 && kra.seconds < 2) {
    console.log('[TIMER] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('[TIMER] Current KRA time:', `${kra.year}-${String(kra.month + 1).padStart(2, '0')}-${String(kra.day).padStart(2, '0')} ${String(kra.hours).padStart(2, '0')}:${String(kra.minutes).padStart(2, '0')}:${String(kra.seconds).padStart(2, '0')}`);
    console.log('[TIMER] Day of week:', day, '(0=Sun, 6=Sat) - isSunday:', day === 0);
    console.log('[TIMER] isSundayBeforeBcast:', isSundayBeforeBcast, 'isSundayLive:', isSundayLive);
    console.log('[TIMER] BCAST_H:', CFG.BCAST_H, 'BCAST_END:', CFG.BCAST_END);
  }

  // Если это воскресное утро, включаем красную мигающую метку у таймера
  const presoonBadge = $('timer-presoon-badge');
  const normalBadge = $('timer-normal-badge');
  if (presoonBadge && normalBadge) {
    const isPresoon = isSundayBeforeBcast;
    presoonBadge.classList.toggle('state-hidden', !isPresoon);
    normalBadge.classList.toggle('state-hidden', isPresoon);
  }

  // Основной обратный отсчёт (days/hours/minutes/seconds)
  let nextYear = kra.year, nextMonth = kra.month, nextDay = kra.day;

  if (isSundayBeforeBcast) {
    // Цель: сегодня 11:00
  } else if (isSundayLive) {
    // Идёт трансляция — отсчёт до СЛЕДУЮЩЕГО воскресенья
    nextDay += 7;
  } else {
    const daysUntilSun = (7 - day) % 7 || 7;
    nextDay += daysUntilSun;
  }

  const nextSunUTC = kraToUTC(nextYear, nextMonth, nextDay, CFG.BCAST_H);
  const diff = Math.max(0, nextSunUTC - nowUTC);

  if (kra.minutes % 10 === 0 && kra.seconds < 2) {
    console.log('[TIMER] Target: воскресенье', nextDay, 'в', CFG.BCAST_H, ':00 (Красноярск)');
    console.log('[TIMER] nextSunUTC:', nextSunUTC, 'nowUTC:', nowUTC, 'diff:', diff, 'ms');
    console.log('[TIMER] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }

  // Класс для анимации изменения цифр
  const setT = (id, v) => {
    const el = $(id);
    if (!el) return;
    if (el.textContent !== v) {
      el.classList.remove('num-pop');
      void el.offsetWidth; // trigger reflow
      el.textContent = v;
      el.classList.add('num-pop');
    }
  };

  setT('days', pad(Math.floor(diff / 86400000)));
  setT('hours', pad(Math.floor((diff % 86400000) / 3600000)));
  setT('minutes', pad(Math.floor((diff % 3600000) / 60000)));
  setT('seconds', pad(Math.floor((diff % 60000) / 1000)));
};

// ── VIDEO ID / IFRAME ────────────────────────────────────────────────────────
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
  link.target = '_blank'; link.rel = 'noopener';
  link.className = 'yt-btn'; link.style.marginTop = '8px';
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

  const _onYTMessage = async (e) => {
    if (!e.data || typeof e.data !== 'string') return;
    try {
      const msg = JSON.parse(e.data);
      if (msg?.event === 'onError' || msg?.info?.errorCode) {
        const errCode = msg?.info?.errorCode ?? 0;
        if (errCode === 101 || errCode === 150) {
          window.removeEventListener('message', _onYTMessage);
          if (container.id === 'live-player') _liveIframeSet = false;
          container.innerHTML = '';
          const ctx = container.id === 'live-player' ? 'live' : 'prev';
          const ok = await _tryRutubeFallback(container, null, ctx);
          if (!ok && ctx === 'live') _showLiveFallback();
        }
      }
    } catch (_) { }
  };
  window.addEventListener('message', _onYTMessage);

  const _loadTimer = setTimeout(() => {
    if (!iframe.contentWindow) {
      window.removeEventListener('message', _onYTMessage);
      _buildEmbedFallback(container, videoId);
    }
  }, 8000);
  iframe.addEventListener('load', () => clearTimeout(_loadTimer), { once: true });
  container.innerHTML = '';
  container.appendChild(iframe);
};

// ── ПОЛУЧЕНИЕ ДАННЫХ ─────────────────────────────────────────────────────────
let _backendCache = null;
const _fetchBackend = async () => {
  if (_backendCache) return _backendCache;
  try {
    const r = await fetch(CFG.BACKEND_URL, { signal: AbortSignal.timeout(5000) });
    if (r.ok) { _backendCache = await r.json(); return _backendCache; }
  } catch (_) { }
  return null;
};

const fetchLiveVideoId = async () => {
  const data = await _fetchBackend();
  if (data?.video_id) {
    const ruBtn = $('live-ru-btn');
    if (ruBtn) ruBtn.href = `https://rutube.ru/video/${encodeURIComponent(data.video_id)}/`;
    return data.video_id;
  }
  return null;
};

const fetchPrevStream = async () => {
  const data = await _fetchBackend();
  if (!data) return null;
  const streams = data.all_streams || [];
  const prev = streams.length >= 2 ? streams[1] : null;
  if (prev?.video_id) return { vid: prev.video_id, title: prev.title || '' };
  return null;
};

// ── RUTUBE ────────────────────────────────────────────────────────────────────
let _rutubeCache = null;
const _fetchRutubeBackend = async () => {
  if (_rutubeCache) return _rutubeCache;
  try {
    const r = await fetch(CFG.RUTUBE_BACKEND_URL, { signal: AbortSignal.timeout(5000) });
    if (r.ok) { _rutubeCache = await r.json(); return _rutubeCache; }
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

const _tryRutubeFallback = async (container, btnEl, context) => {
  const data = await _fetchRutubeBackend();
  if (!data?.video_id) return false;
  const streams = data.all_streams || [];
  let target;
  if (context === 'prev') {
    target = (data.is_live && streams.length >= 2) ? streams[1] : (streams[0] || data);
  } else {
    target = streams[0] || data;
  }
  if (!target?.video_id) return false;
  buildRutubeIframe(container, target.video_id, context === 'live');
  const ruBtn = $('live-ru-btn');
  if (ruBtn) ruBtn.href = `https://rutube.ru/video/${encodeURIComponent(target.video_id)}/`;
  return true;
};

// ── DETECT STATE ─────────────────────────────────────────────────────────────
let _liveVideoId = null;
let _liveIframeSet = false;
let _lastDetectState = null;

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
    <a href="${CFG.YT_CHANNEL_URL}/live" target="_blank" rel="noopener" class="yt-btn" style="text-decoration:none">Смотреть на YouTube</a>
  </div>`;
};

const detectState = async () => {
  const kra = getKraComponents();
  const day = kra.dayOfWeek;
  const h = kra.hours;
  const m = kra.minutes;
  const inWindow = day === 0 && h >= CFG.BCAST_H && h < CFG.BCAST_END;
  const isBefore = day === 0 && h < CFG.BCAST_H;

  const currentState = inWindow ? 'LIVE' : (isBefore ? 'SOON' : 'WAIT');
  if (currentState !== _lastDetectState) {
    console.log(`[TIMER] State changed: ${_lastDetectState || 'INIT'} -> ${currentState}`);
    _lastDetectState = currentState;
  }

  if (inWindow) {
    showTimerState('live');
    if (_liveIframeSet) return;
    _showLiveFallback();
    const lp = $('live-player');

    // Rutube (приоритет)
    const ruLiveData = await _fetchRutubeBackend();
    const ruLiveStreams = ruLiveData?.all_streams || [];
    const ruLiveTarget = ruLiveStreams[0] || (ruLiveData?.video_id ? ruLiveData : null);
    if (ruLiveTarget?.video_id) {
      buildRutubeIframe(lp, ruLiveTarget.video_id, true);
      _liveVideoId = ruLiveTarget.video_id;
      _liveIframeSet = true;
      const ld = $('live-date');
      if (ld) ld.textContent = ruLiveTarget.title || new Date().toLocaleString('ru-RU', {
        timeZone: CFG.TZ, hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'long',
      });
      const ruBtn = $('live-ru-btn');
      if (ruBtn) ruBtn.href = `https://rutube.ru/video/${encodeURIComponent(ruLiveTarget.video_id)}/`;
      console.log('[TIMER] Loaded Rutube stream:', ruLiveTarget.video_id);
      return;
    }

    // YouTube (резерв)
    const vid = await fetchLiveVideoId();
    if (vid) {
      _liveVideoId = vid;
      _liveIframeSet = true;
      buildIframe(lp, vid, true);
      const ld = $('live-date');
      if (ld) ld.textContent = new Date().toLocaleString('ru-RU', {
        timeZone: CFG.TZ, hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'long',
      });
      console.log('[TIMER] Loaded YouTube stream:', vid);
    }
    return;
  }

  if (_liveIframeSet) {
    _liveIframeSet = false; _liveVideoId = null;
    const lp = $('live-player');
    if (lp) lp.innerHTML = '';
    console.log('[TIMER] Cleared live player');
  }
  showTimerState('timer');
};


// ── СОБЫТИЯ (СЛАЙДЕР) ──────────────────────────────────────────────────────────
const initEventsSlider = () => {
  const slider = $('eventsSlider');
  const dotsWrap = $('eventsDots');
  if (!slider || !dotsWrap) return;
  const slides = Array.from(slider.querySelectorAll('.event-slide'));
  if (slides.length <= 1) return;

  slides.forEach((_, i) => {
    const d = document.createElement('button');
    d.className = 'hero-dot' + (i === 0 ? ' active' : '');
    d.setAttribute('role', 'tab');
    d.setAttribute('aria-label', 'Событие ' + (i + 1));
    d.addEventListener('click', () => {
      slider.scrollTo({
        left: slides[i].offsetLeft - (slider.clientWidth / 2) + (slides[i].clientWidth / 2),
        behavior: 'smooth'
      });
    });
    dotsWrap.appendChild(d);
  });

  const dots = Array.from(dotsWrap.querySelectorAll('.hero-dot'));
  slider.addEventListener('scroll', () => {
    let focusCenter = slider.scrollLeft + slider.clientWidth / 2;
    let minDiff = Infinity;
    let activeIdx = 0;
    slides.forEach((slide, i) => {
      let slideCenter = slide.offsetLeft + slide.clientWidth / 2;
      let diff = Math.abs(focusCenter - slideCenter);
      if (diff < minDiff) { minDiff = diff; activeIdx = i; }
    });
    dots.forEach((d, i) => d.classList.toggle('active', i === activeIdx));
  }, { passive: true });
};

// ── ЗАПУСК ИНТЕРВАЛОВ ────────────────────────────────────────────────────────
const startIntervals = () => {
  clearAllIntervals();
  addInterval('clock', updateClock, 10000);
  addInterval('countdown', updateCountdown, 1000);
  const kra = getKraComponents();
  const inWindow = kra.dayOfWeek === 0 && kra.hours >= CFG.BCAST_H && kra.hours < CFG.BCAST_END;
  addInterval('detect', detectState, inWindow ? 15000 : 60000);
};

// ── ИНИЦИАЛИЗАЦИЯ ────────────────────────────────────────────────────────────
const init = () => {
  // Initial state
  Object.values(STATE_IDS).forEach(id => {
    const el = $(id);
    if (el) { el.classList.add('state-hidden'); el.setAttribute('aria-hidden', 'true'); }
  });
  showTimerState('timer');

  updateClock();
  updateCountdown();
  detectState();
  startIntervals();
  initNav();
  initEventsSlider();
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
