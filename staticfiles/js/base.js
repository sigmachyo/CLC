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
