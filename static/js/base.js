/**
 * Глобальная логика приложения KCLC
 */
document.addEventListener('DOMContentLoaded', function () {
    // ── Инициализация модальных окон
    initModals();
    // ── Инициализация подсказок (Tooltips)
    initTooltips();
    // ── Инициализация взаимодействия с уровнями (для страницы карты)
    if (document.querySelector('.level-node')) {
        initLevelInteractions();
    }
    // ── Push-уведомления
    if ('Notification' in window && navigator.serviceWorker) {
        initPushNotifications();
    }
    // ── Защита форм от повторной отправки
    initFormProtection();
    // ── Smart Header
    initSmartHeader();
});

/**
 * Глобальный обработчик ошибок
 */
window.addEventListener('error', function(event) {
    console.error('JS Runtime Error:', event.error || event.message);
    // Можно отправлять на сервер или выводить тост в режиме отладки
});
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled Promise Rejection:', event.reason);
});

/**
 * Модальные окна
 */
function initModals() {
    const modal = document.getElementById('levelModal');
    if (!modal) return;
    const closeBtn = modal.querySelector('.modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => modal.classList.remove('show'));
    }
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('show');
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('show')) {
            modal.classList.remove('show');
        }
    });
}
/**
 * Подсказки
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const text = this.getAttribute('data-tooltip');
            if (!text) return;
            const tooltip = document.createElement('div');
            tooltip.className = 'fixed bg-navy text-white text-[10px] px-3 py-1.5 rounded-lg shadow-xl z-[10000] pointer-events-none opacity-0 transition-opacity duration-200 uppercase font-bold tracking-widest';
            tooltip.textContent = text;
            document.body.appendChild(tooltip);
            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
            tooltip.style.left = (rect.left + rect.width/2 - tooltip.offsetWidth/2) + 'px';
            requestAnimationFrame(() => tooltip.classList.add('opacity-100'));
            this._tooltip = tooltip;
        });
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                delete this._tooltip;
            }
        });
    });
}
/**
 * Взаимодействие с уровнями
 */
function initLevelInteractions() {
    const levelNodes = document.querySelectorAll('.level-node:not(.locked)');
    levelNodes.forEach(node => {
        node.addEventListener('mouseenter', function() {
            if (!this.classList.contains('completed')) {
                this.style.transform = 'translateY(-5px)';
            }
        });
        node.addEventListener('mouseleave', function() {
            if (!this.classList.contains('completed')) {
                this.style.transform = 'translateY(0)';
            }
        });
    });
}
/**
 * Push уведомления
 */
function initPushNotifications() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
    
    const applicationServerKey = urlB64ToUint8Array('BPWzM8Sg21koEirpUOKjfqqqUeOL6c4PrF3KwT32QYT9pQP6R1Da9u8jSS0UMTkx4DL_75iOadzTAPNSOJVGlpo');
    
    navigator.serviceWorker.ready.then(reg => {
        reg.pushManager.getSubscription().then(sub => {
            if (sub) {
                // Если уже подписан - синхронизируем с сервером
                sendSubscriptionToBackend(sub);
            } else if (Notification.permission === 'granted') {
                // Если разрешение есть, но подписки нет (например, устарела)
                reg.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: applicationServerKey
                })
                .then(newSub => sendSubscriptionToBackend(newSub))
                .catch(e => console.error('Push subscription failed:', e));
            }
        });
    });
}

// Вызывается вручную по клику на кнопку в профиле
window.subscribeToPush = function() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        showNotification('Уведомления не поддерживаются вашим браузером', 'error');
        return;
    }
    return Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
            const applicationServerKey = urlB64ToUint8Array('BPWzM8Sg21koEirpUOKjfqqqUeOL6c4PrF3KwT32QYT9pQP6R1Da9u8jSS0UMTkx4DL_75iOadzTAPNSOJVGlpo');
            return navigator.serviceWorker.ready.then(reg => {
                return reg.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: applicationServerKey
                })
                .then(newSub => {
                    sendSubscriptionToBackend(newSub);
                    showNotification('Уведомления успешно включены', 'success');
                    return true;
                })
                .catch(e => {
                    console.error('Push subscription error:', e);
                    showNotification('Ошибка при подписке на уведомления', 'error');
                    return false;
                });
            });
        } else {
            showNotification('Вы запретили показ уведомлений', 'error');
            return false;
        }
    });
};

window.unsubscribeFromPush = function() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return Promise.resolve(false);
    
    return navigator.serviceWorker.ready.then(reg => {
        return reg.pushManager.getSubscription().then(subscription => {
            if (subscription) {
                return subscription.unsubscribe().then(successful => {
                    if (successful) {
                        // Можно также отправить запрос на бэкенд для удаления подписки из БД
                        showNotification('Уведомления отключены', 'success');
                        return true;
                    }
                    return false;
                });
            }
            return true;
        });
    });
};

function urlB64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

function sendSubscriptionToBackend(subscription) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) return;

    fetch('/api/push/subscribe/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(subscription)
    })
    .then(res => res.json())
    .then(data => console.log('Push subscription saved'))
    .catch(err => console.error('Push save err:', err));
}
/**
 * Системные уведомления (Toast)
 */
function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed top-6 right-6 px-6 py-4 rounded-2xl shadow-2xl z-[10000] flex items-center gap-4 transition-all duration-300 translate-x-[150%] border-l-4 ${
        type === 'success' ? 'bg-white border-green-500' : 'bg-white border-red-500'
    }`;
    const icon = type === 'success' ? 'check_circle' : 'warning';
    const iconColor = type === 'success' ? 'text-green-500' : 'text-red-500';
    toast.innerHTML = `
        <span class="material-symbols-outlined ${iconColor}">${icon}</span>
        <span class="text-navy font-medium text-sm">${message}</span>
    `;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.remove('translate-x-[150%]'));
    setTimeout(() => {
        toast.classList.add('translate-x-[150%]');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/**
 * Защита от повторной отправки форм
 */
function initFormProtection() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (this.dataset.submitting === 'true') {
                e.preventDefault();
                return;
            }
            this.dataset.submitting = 'true';
            const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                // Небольшая задержка, чтобы submit прошел
                setTimeout(() => {
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.7';
                    submitBtn.style.cursor = 'not-allowed';
                    if (submitBtn.tagName === 'BUTTON') {
                        submitBtn.dataset.originalText = submitBtn.innerHTML;
                        submitBtn.innerHTML = 'Обработка...';
                    } else if (submitBtn.tagName === 'INPUT') {
                        submitBtn.dataset.originalValue = submitBtn.value;
                        submitBtn.value = 'Обработка...';
                    }
                }, 0);
            }
        });
    });
}

/**
 * Smart Header - Мягкое скрытие при скролле вниз и появление при скролле вверх
 */
function initSmartHeader() {
    const header = document.querySelector('.kclc-header');
    if (!header) return;

    let lastScrollY = 0;
    let ticking = false;

    function getScrollPos(target) {
        if (target && target !== window && target !== document && typeof target.scrollTop === 'number' && target.scrollTop > 0) {
            return target.scrollTop;
        }
        const snap = document.getElementById('snap-root');
        if (snap && typeof snap.scrollTop === 'number' && snap.scrollTop > 0) {
            return snap.scrollTop;
        }
        return window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
    }

    function handleScroll(e) {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const target = (e && e.target && e.target !== document) ? e.target : window;
                const currentScrollY = getScrollPos(target);
                const diff = currentScrollY - lastScrollY;

                // Если прокрутили вниз более чем на 8px и мы ниже шапки (> 60px)
                if (diff > 8 && currentScrollY > 60) {
                    header.classList.add('header-hidden');
                } else if (diff < -8 || currentScrollY <= 25) {
                    // При скролле вверх или возврате к самому верху плавно показываем
                    header.classList.remove('header-hidden');
                }

                if (currentScrollY >= 0) {
                    lastScrollY = currentScrollY;
                }
                ticking = false;
            });
            ticking = true;
        }
    }

    // Слушаем скролл и на window, и на document (capture phase для snap-root), и конкретно на #snap-root
    window.addEventListener('scroll', handleScroll, { passive: true });
    document.addEventListener('scroll', handleScroll, { capture: true, passive: true });

    const snapRoot = document.getElementById('snap-root');
    if (snapRoot) {
        snapRoot.addEventListener('scroll', handleScroll, { passive: true });
    }
}

/**
 * Тестовое Push-уведомление — немедленная проверка на смартфоне
 */
window.sendTestPushNotification = async function() {
    if (!('serviceWorker' in navigator)) {
        showNotification('Service Worker не поддерживается вашим браузером', 'error');
        return;
    }

    // 1. Проверяем/запрашиваем разрешение
    if (Notification.permission === 'denied') {
        showNotification('Уведомления заблокированы. Разрешите их в настройках браузера (иконка замка в адресной строке)', 'error');
        return;
    }

    if (Notification.permission !== 'granted') {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            showNotification('Вы не разрешили уведомления', 'error');
            return;
        }
    }

    try {
        // 2. Тактильный виброотклик смартфона
        if ('vibrate' in navigator) {
            try { navigator.vibrate([200, 100, 200]); } catch(e) {}
        }

        // 3. Локальный мгновенный пуш через Service Worker (всегда работает)
        const reg = await navigator.serviceWorker.ready;
        await reg.showNotification('Церковь KCLC Красноярск 🕊️', {
            body: 'Тестовое уведомление! Уведомления на вашем смартфоне работают безупречно!',
            icon: '/static/icons/apple-touch-icon.png',
            badge: '/static/icons/favicon-32x32.png',
            vibrate: [200, 100, 200],
            data: { url: '/profile/' },
            tag: 'test-push-' + Date.now(),
        });

        showNotification('🔔 Проверьте шторку уведомлений на телефоне!', 'success');

        // 3. Также отправляем серверный пуш для проверки полного цикла
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            // Получаем endpoint текущей подписки для передачи серверу
            let endpoint = '';
            try {
                const sub = await reg.pushManager.getSubscription();
                if (sub) endpoint = sub.endpoint;
            } catch(e) { /* ignore */ }

            fetch('/api/push/test/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ endpoint })
            }).catch(() => { /* server push is optional bonus */ });
        }
    } catch (err) {
        console.error('Test push error:', err);
        showNotification('Ошибка при отправке тестового уведомления', 'error');
    }
};
