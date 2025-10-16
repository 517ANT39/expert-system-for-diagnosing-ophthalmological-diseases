// Функции для регистрации и авторизации

async function registerDoctor(formData) {
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Регистрация успешна! Теперь вы можете войти в систему.', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Ошибка соединения с сервером', 'error');
    }
}

async function loginDoctor(formData) {
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Вход выполнен успешно!', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Ошибка соединения с сервером', 'error');
    }
}

function showNotification(message, type = 'info') {
    // Простая реализация уведомлений
    alert(`${type.toUpperCase()}: ${message}`);
}

// Обработчики для форм
document.addEventListener('DOMContentLoaded', function() {
    // Регистрация
    const registerForm = document.querySelector('.login-form');
    if (registerForm && window.location.pathname === '/registration') {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                last_name: document.getElementById('last_name').value,
                first_name: document.getElementById('first_name').value,
                middle_name: document.getElementById('middle_name').value,
                email: document.getElementById('email').value,
                phone: document.getElementById('phone').value,
                password: document.getElementById('password').value,
                confirm_password: document.getElementById('confirmPassword').value
            };
            
            registerDoctor(formData);
        });
    }
    
    // Авторизация
    const loginForm = document.querySelector('.login-form');
    if (loginForm && window.location.pathname === '/login') {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                email: document.getElementById('email').value,
                password: document.getElementById('password').value
            };
            
            loginDoctor(formData);
        });
    }
});