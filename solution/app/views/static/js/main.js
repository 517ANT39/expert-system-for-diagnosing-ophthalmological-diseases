// Main application functionality
class OphthalmologyExpertSystem {
    constructor() {
        this.currentUser = null;
        this.settings = {};
        this.init();
    }

    init() {
        this.loadSettings();
        this.setupServiceWorker();
        this.setupGlobalHandlers();
        this.checkAuth();
    }

    loadSettings() {
        // Load user settings from localStorage
        const savedSettings = localStorage.getItem('app_settings');
        if (savedSettings) {
            this.settings = JSON.parse(savedSettings);
        } else {
            this.settings = {
                theme: 'light',
                language: 'ru',
                notifications: true,
                autoSave: true
            };
        }

        this.applySettings();
    }

    applySettings() {
        // Apply theme
        document.documentElement.setAttribute('data-theme', this.settings.theme);
        
        // Apply other settings
        if (this.settings.language) {
            document.documentElement.lang = this.settings.language;
        }
    }

    setupServiceWorker() {
        // Register service worker for PWA functionality
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('SW registered: ', registration);
                })
                .catch(registrationError => {
                    console.log('SW registration failed: ', registrationError);
                });
        }
    }

    setupGlobalHandlers() {
        // Global error handler
        window.addEventListener('error', this.handleGlobalError.bind(this));
        
        // Online/offline detection
        window.addEventListener('online', this.handleOnline.bind(this));
        window.addEventListener('offline', this.handleOffline.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    }

    handleGlobalError(event) {
        console.error('Global error:', event.error);
        // In production, send to error tracking service
    }

    handleOnline() {
        this.showToast('Соединение восстановлено', 'success');
    }

    handleOffline() {
        this.showToast('Отсутствует интернет-соединение', 'warning');
    }

    handleKeyboardShortcuts(event) {
        // Global keyboard shortcuts
        const isInputFocused = event.target.tagName === 'INPUT' || 
                              event.target.tagName === 'TEXTAREA' ||
                              event.target.isContentEditable;

        if (isInputFocused) return;

        switch(event.key) {
            case '?':
                event.preventDefault();
                this.showKeyboardShortcuts();
                break;
            case 'Escape':
                this.closeModals();
                break;
        }
    }

    showKeyboardShortcuts() {
        const shortcuts = [
            { key: '?', action: 'Показать эту справку' },
            { key: 'Escape', action: 'Закрыть модальные окна' },
            { key: 'Ctrl + S', action: 'Сохранить' },
            { key: 'Ctrl + /', action: 'Быстрый поиск' }
        ];

        const shortcutsHTML = shortcuts.map(shortcut => `
            <div class="shortcut-item">
                <kbd>${shortcut.key}</kbd>
                <span>${shortcut.action}</span>
            </div>
        `).join('');

        this.showModal('Сочетания клавиш', shortcutsHTML);
    }

    checkAuth() {
        // Check if user is authenticated
        const token = localStorage.getItem('auth_token');
        if (token) {
            this.validateToken(token);
        } else {
            this.redirectToLogin();
        }
    }

    async validateToken(token) {
        try {
            // Simulate token validation
            const userData = await this.verifyToken(token);
            this.currentUser = userData;
            this.setupUserSession(userData);
        } catch (error) {
            this.redirectToLogin();
        }
    }

    async verifyToken(token) {
        // Simulate API call
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    id: 1,
                    name: 'Доктор Иванов',
                    email: 'doctor@example.com',
                    role: 'ophthalmologist',
                    permissions: ['read', 'write', 'consult']
                });
            }, 100);
        });
    }

    setupUserSession(userData) {
        // Update UI based on user role and permissions
        this.updateUserInterface(userData);
        
        // Start session timer
        this.startSessionTimer();
    }

    updateUserInterface(userData) {
        // Update user name in navigation
        const userElements = document.querySelectorAll('.user-name');
        userElements.forEach(element => {
            element.textContent = userData.name;
        });

        // Show/hide elements based on permissions
        this.applyPermissions(userData.permissions);
    }

    applyPermissions(permissions) {
        // Example: Hide admin features for non-admin users
        if (!permissions.includes('admin')) {
            const adminElements = document.querySelectorAll('[data-requires-admin]');
            adminElements.forEach(element => {
                element.style.display = 'none';
            });
        }
    }

    startSessionTimer() {
        // Session timeout after 2 hours
        this.sessionTimer = setTimeout(() => {
            this.logout('Сессия истекла. Пожалуйста, войдите снова.');
        }, 2 * 60 * 60 * 1000); // 2 hours
    }

    logout(message = 'Вы вышли из системы') {
        localStorage.removeItem('auth_token');
        this.showToast(message, 'info');
        this.redirectToLogin();
    }

    redirectToLogin() {
        if (!window.location.href.includes('login.html')) {
            window.location.href = 'login.html';
        }
    }

    showToast(message, type = 'info') {
        // Reuse toast functionality
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'warning' ? '#FEF3C7' : 
                       type === 'error' ? '#FEE2E2' : 
                       type === 'success' ? '#D1FAE5' : '#DBEAFE',
            color: type === 'warning' ? '#D97706' : 
                   type === 'error' ? '#DC2626' : 
                   type === 'success' ? '#059669' : '#1E40AF',
            padding: '1rem 1.5rem',
            borderRadius: 'var(--border-radius)',
            border: `1px solid ${
                type === 'warning' ? '#FCD34D' : 
                type === 'error' ? '#FECACA' : 
                type === 'success' ? '#A7F3D0' : '#93C5FD'
            }`,
            zIndex: '1000',
            boxShadow: 'var(--shadow-md)'
        });

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    showModal(title, content) {
        // Simple modal implementation
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-content">
                    ${content}
                </div>
            </div>
        `;

        Object.assign(modal.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            right: '0',
            bottom: '0',
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: '10000'
        });

        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        document.body.appendChild(modal);
    }

    closeModals() {
        const modals = document.querySelectorAll('.modal-overlay');
        modals.forEach(modal => modal.remove());
    }

    // Utility methods
    formatDate(date) {
        return new Date(date).toLocaleDateString('ru-RU');
    }

    formatDateTime(date) {
        return new Date(date).toLocaleString('ru-RU');
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // API methods
    async apiCall(endpoint, options = {}) {
        const baseURL = 'https://api.ophthalmology-expert.com';
        const token = localStorage.getItem('auth_token');
        
        const config = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(`${baseURL}${endpoint}`, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.app = new OphthalmologyExpertSystem();
});

// Utility functions for global use
const AppUtils = {
    // Format medical terms
    formatDiagnosis(diagnosis) {
        return diagnosis.charAt(0).toUpperCase() + diagnosis.slice(1).toLowerCase();
    },

    // Calculate patient age
    calculateAge(birthDate) {
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const monthDiff = today.getMonth() - birth.getMonth();
        
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            age--;
        }
        
        return age;
    },

    // Validate medical data
    validateMedicalData(data) {
        const errors = [];
        
        if (data.systolicBP && data.diastolicBP) {
            if (data.systolicBP < 60 || data.systolicBP > 250) {
                errors.push('Систолическое давление вне допустимого диапазона');
            }
            if (data.diastolicBP < 40 || data.diastolicBP > 150) {
                errors.push('Диастолическое давление вне допустимого диапазона');
            }
        }
        
        return errors;
    },

    // Generate patient ID
    generatePatientId() {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 5);
        return `PAT${timestamp}${random}`.toUpperCase();
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OphthalmologyExpertSystem, AppUtils };
}