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
    // Только если пользователь авторизован (но это проверяется на сервере)
    const applicationServerKey = 'BPWzM8Sg21koEirpUOKjfqqqUeOL6c4PrF3KwT32QYT9pQP6R1Da9u8jSS0UMTkx4DL_75iOadzTAPNSOJVGlpo';
    navigator.serviceWorker.ready.then(reg => {
        reg.pushManager.getSubscription().then(sub => {
            if (sub) return; // Уже подписан
            // Если нужно - подписываем (можно добавить кнопку специальную)
            // reg.pushManager.subscribe({ ... });
        });
    });
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
