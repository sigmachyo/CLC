document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    const levelCards = document.querySelectorAll('.level-card');
    function initLevelCards() {
        levelCards.forEach(card => {
            card.removeEventListener('click', handleCardClick);
            card.addEventListener('click', handleCardClick);
        });
    }
    function handleCardClick(e) {
        const card = e.currentTarget;
        const levelId = card.dataset.levelId;
        if (card.classList.contains('locked')) {
            e.preventDefault();
            showNotification('❌ Этот уровень пока недоступен', 'error');
            return;
        }
        animateCardClick(card);
        setTimeout(() => {
            window.location.href = `/level/${levelId}/`;
        }, 300);
    }
    function animateCardClick(card) {
        card.style.transform = 'scale(0.95)';
        setTimeout(() => {
            card.style.transform = '';
        }, 200);
    }
    function showNotification(message, type = 'info') {
        let notificationContainer = document.querySelector('.notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.className = 'notification-container';
            notificationContainer.style.cssText = `
                position: fixed;
                top: 100px;
                right: 30px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(notificationContainer);
        }
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            background: ${type === 'error' ? 'rgba(231, 76, 60, 0.95)' : 'rgba(46, 204, 113, 0.95)'};
            color: white;
            padding: 15px 25px;
            border-radius: 50px;
            font-weight: 600;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
        `;
        notification.textContent = message;
        notificationContainer.appendChild(notification);
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
    function animateProgressBar() {
        const progressFill = document.querySelector('.progress-bar-fill');
        if (progressFill) {
            const width = progressFill.style.width;
            progressFill.style.width = '0%';
            setTimeout(() => {
                progressFill.style.width = width;
            }, 100);
        }
    }
    function initParallax() {
        const mapContainer = document.querySelector('.map-container');
        if (!mapContainer) return;
        let controller = null;
        function attachParallax() {
            if (window.innerWidth > 768) {
                if (controller) return; // уже подключено
                controller = new AbortController();
                window.addEventListener('mousemove', function(e) {
                    const x = e.clientX / window.innerWidth;
                    const y = e.clientY / window.innerHeight;
                    mapContainer.style.backgroundPosition = `${50 + (x - 0.5) * 20}% ${30 + (y - 0.5) * 20}%`;
                }, { signal: controller.signal, passive: true });
            } else {
                if (controller) {
                    controller.abort();
                    controller = null;
                    mapContainer.style.backgroundPosition = '';
                }
            }
        }
        attachParallax();
        window.addEventListener('resize', attachParallax, { passive: true });
    }
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
    function initCardsAnimation() {
        levelCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            card.style.transition = 'all 0.5s ease';
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }
    function initLockedLevels() {
        const lockedCards = document.querySelectorAll('.level-card.locked');
        lockedCards.forEach(card => {
            card.setAttribute('title', 'Завершите предыдущие уровни чтобы открыть этот');
        });
    }
    function addAnimationStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            .level-card.completed {
                animation: pulse 2s infinite;
            }
        `;
        document.head.appendChild(style);
    }
    function init() {
        initLevelCards();
        initCardsAnimation();
        initLockedLevels();
        initSmoothScroll();
        initParallax();
        addAnimationStyles();
        animateProgressBar();
    }
    init();
});