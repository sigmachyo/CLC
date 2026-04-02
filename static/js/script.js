// Основной JavaScript файл

document.addEventListener('DOMContentLoaded', function() {
    console.log('Духовный Путь загружен!');
    
    // Добавляем обработчики для всех интерактивных элементов
    initModals();
    initTooltips();
    initLevelInteractions();
    
    // Запрос разрешений на Push
    if ('Notification' in window && navigator.serviceWorker) {
        initPushNotifications();
    }
});

// Инициализация модальных окон
function initModals() {
    const modal = document.getElementById('levelModal');
    if (!modal) return;
    
    const modalClose = modal.querySelector('.modal-close');
    
    // Закрытие по крестику
    if (modalClose) {
        modalClose.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // Закрытие по клику вне окна
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Закрытие по ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            modal.style.display = 'none';
        }
    });
}

// Всплывающие подсказки
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltipText = this.getAttribute('data-tooltip');
            if (!tooltipText) return;
            
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = tooltipText;
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.position = 'fixed';
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
            tooltip.style.left = (rect.left + rect.width/2 - tooltip.offsetWidth/2) + 'px';
            
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

// Взаимодействие с уровнями
function initLevelInteractions() {
    const levelNodes = document.querySelectorAll('.level-node:not(.locked)');
    
    levelNodes.forEach(node => {
        // Эффект при наведении
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
        
        // Анимация клика
        node.addEventListener('mousedown', function() {
            this.style.transform = 'translateY(-2px) scale(0.98)';
        });
        
        node.addEventListener('mouseup', function() {
            this.style.transform = 'translateY(-5px)';
        });
    });
}

// Push уведомления
function initPushNotifications() {
    Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
            console.log('Push разрешение получено.');
            // В реальном приложении здесь делается подписка 
            // navigator.serviceWorker.ready.then(reg => reg.pushManager.subscribe(...))
            // и отправка endpoint + keys на сервер /api/push/subscribe/
        }
    });
}

// Утилиты
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Анимация появления
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Автоматическое скрытие
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Добавляем стили для уведомлений
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    border-radius: 12px;
    background: white;
    box-shadow: 0 5px 20px rgba(0,0,0,0.15);
    display: flex;
    align-items: center;
    gap: 10px;
    z-index: 10000;
    transform: translateX(150%);
    transition: transform 0.3s ease;
    max-width: 350px;
}

.notification.show {
    transform: translateX(0);
}

.notification-success {
    border-left: 4px solid #2ecc71;
}

.notification-error {
    border-left: 4px solid #e74c3c;
}

.notification i {
    font-size: 1.2rem;
}

.notification-success i {
    color: #2ecc71;
}

.notification-error i {
    color: #e74c3c;
}
`;

document.head.appendChild(notificationStyles);