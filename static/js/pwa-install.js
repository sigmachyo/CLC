/**
 * PWA Install Banner — KCLC
 *
 * Логика показа:
 * - Если localStorage['pwa-never-show'] = 'true' → никогда не показывать
 * - Если sessionStorage['pwa-dismissed-session'] = 'true' → не показывать в этой сессии
 * - Иначе — показать баннер при срабатывании beforeinstallprompt
 *
 * Кнопки:
 * 1. «Добавить» — вызывает системный промпт установки
 * 2. «Убрать на этот раз» — скрывает на сессию (sessionStorage)
 * 3. «Больше не показывать» — скрывает навсегда (localStorage)
 */

(function () {
    'use strict';

    const LS_KEY = 'pwa-never-show';
    const SS_KEY = 'pwa-dismissed-session';

    let deferredPrompt = null;
    let bannerEl = null;

    // ── Создаём DOM баннера
    function createBanner() {
        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.setAttribute('role', 'dialog');
        banner.setAttribute('aria-label', 'Установить приложение KCLC');
        banner.innerHTML = `
            <div class="pwa-banner-inner">
                <div class="pwa-banner-icon">
                    <img src="/static/icons/icon-192x192.png" alt="KCLC" width="48" height="48">
                </div>
                <div class="pwa-banner-text">
                    <strong>Добавить KCLC на главный экран</strong>
                    <span>Быстрый доступ без браузера</span>
                </div>
                <div class="pwa-banner-actions">
                    <button id="pwa-btn-add" class="pwa-btn pwa-btn-primary" aria-label="Добавить приложение на главный экран">
                        Добавить
                    </button>
                    <button id="pwa-btn-dismiss" class="pwa-btn pwa-btn-secondary" aria-label="Скрыть на этот раз">
                        Убрать на этот раз
                    </button>
                    <button id="pwa-btn-never" class="pwa-btn pwa-btn-text" aria-label="Больше не показывать">
                        Больше не показывать
                    </button>
                </div>
            </div>
        `;

        // Инжектируем CSS прямо здесь чтобы не зависеть от порядка загрузки стилей
        const style = document.createElement('style');
        style.textContent = `
            #pwa-install-banner {
                position: fixed;
                bottom: 80px; /* над bottom-nav */
                left: 50%;
                transform: translateX(-50%) translateY(120%);
                z-index: 9999;
                width: calc(100% - 2rem);
                max-width: 480px;
                background: #1a1f36;
                border: 1px solid rgba(201, 168, 76, 0.3);
                border-radius: 1rem;
                padding: 1rem;
                box-shadow: 0 8px 40px rgba(0,0,0,0.4);
                transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
                font-family: 'Public Sans', sans-serif;
            }
            #pwa-install-banner.pwa-visible {
                transform: translateX(-50%) translateY(0);
            }
            .pwa-banner-inner {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 0.75rem;
            }
            .pwa-banner-icon img {
                border-radius: 0.5rem;
                flex-shrink: 0;
            }
            .pwa-banner-text {
                flex: 1;
                min-width: 120px;
                display: flex;
                flex-direction: column;
                gap: 2px;
            }
            .pwa-banner-text strong {
                color: #c9a84c;
                font-size: 0.9rem;
                font-weight: 700;
            }
            .pwa-banner-text span {
                color: rgba(255,255,255,0.6);
                font-size: 0.78rem;
            }
            .pwa-banner-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                width: 100%;
                margin-top: 0.25rem;
            }
            .pwa-btn {
                border: none;
                border-radius: 0.5rem;
                font-size: 0.82rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                padding: 0.5rem 0.9rem;
                font-family: inherit;
            }
            .pwa-btn-primary {
                background: #c9a84c;
                color: #1a1f36;
                flex: 1;
            }
            .pwa-btn-primary:hover {
                background: #b08e35;
                transform: translateY(-1px);
            }
            .pwa-btn-secondary {
                background: rgba(255,255,255,0.08);
                color: rgba(255,255,255,0.8);
                flex: 1;
            }
            .pwa-btn-secondary:hover {
                background: rgba(255,255,255,0.15);
            }
            .pwa-btn-text {
                background: transparent;
                color: rgba(255,255,255,0.4);
                font-size: 0.75rem;
                padding: 0.4rem;
                width: 100%;
                text-align: center;
            }
            .pwa-btn-text:hover {
                color: rgba(255,255,255,0.7);
            }
            @media (min-width: 640px) {
                #pwa-install-banner {
                    bottom: 2rem;
                }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(banner);
        return banner;
    }

    // ── Показываем баннер с анимацией
    function showBanner() {
        if (!bannerEl) bannerEl = createBanner();

        // Небольшая задержка чтобы transition сработал
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                bannerEl.classList.add('pwa-visible');
            });
        });

        // Кнопка «Добавить»
        document.getElementById('pwa-btn-add').addEventListener('click', async () => {
            hideBanner();
            if (!deferredPrompt) return;
            try {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                console.log('[PWA] User choice:', outcome);
            } catch (e) {
                console.warn('[PWA] Install prompt error:', e);
            }
            deferredPrompt = null;
        });

        // Кнопка «Убрать на этот раз» → sessionStorage
        document.getElementById('pwa-btn-dismiss').addEventListener('click', () => {
            sessionStorage.setItem(SS_KEY, 'true');
            hideBanner();
        });

        // Кнопка «Больше не показывать» → localStorage
        document.getElementById('pwa-btn-never').addEventListener('click', () => {
            localStorage.setItem(LS_KEY, 'true');
            hideBanner();
        });
    }

    // ── Скрываем баннер с анимацией
    function hideBanner() {
        if (!bannerEl) return;
        bannerEl.classList.remove('pwa-visible');
    }

    // ── Проверяем, нужно ли показывать баннер
    function shouldShow() {
        if (localStorage.getItem(LS_KEY) === 'true') return false;
        if (sessionStorage.getItem(SS_KEY) === 'true') return false;
        // Не показываем если уже установлено как PWA
        if (window.matchMedia('(display-mode: standalone)').matches) return false;
        if (window.navigator.standalone === true) return false;
        return true;
    }

    // ── Перехватываем событие beforeinstallprompt
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault(); // Предотвращаем автоматический промпт браузера
        deferredPrompt = e;

        if (shouldShow()) {
            // Небольшая задержка перед показом — чтобы страница успела загрузиться
            setTimeout(showBanner, 2000);
        }
    });

    // ── Если приложение успешно установлено — скрываем баннер навсегда
    window.addEventListener('appinstalled', () => {
        localStorage.setItem(LS_KEY, 'true');
        hideBanner();
        console.log('[PWA] App installed successfully');
    });

})();
