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

// Функция для загрузки данных профиля
async function loadProfileData() {
    try {
        console.log('Loading profile data from:', '/api/profile');
        const response = await fetch('/api/profile', {
            credentials: 'same-origin' // Важно для отправки сессии
        });
        
        if (response.status === 401) {
            console.log('User not authenticated, redirecting to login');
            window.location.href = '/login';
            return;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Profile response:', result);

        if (result.success) {
            const doctor = result.doctor;
            console.log('Doctor data loaded:', doctor);
            
            // Обновляем данные в навигации
            const userNameElements = document.querySelectorAll('.user-name');
            userNameElements.forEach(element => {
                element.textContent = `${doctor.first_name} ${doctor.last_name}`;
                console.log('Updated user name to:', `${doctor.first_name} ${doctor.last_name}`);
            });
            
            // Обновляем данные профиля
            if (document.getElementById('doctorFullName')) {
                document.getElementById('doctorFullName').textContent = 
                    `${doctor.last_name} ${doctor.first_name} ${doctor.middle_name || ''}`.trim();
                document.getElementById('doctorEmail').textContent = doctor.email;
                document.getElementById('doctorPhone').textContent = doctor.phone || 'Не указан';
                
                // Форматируем дату регистрации
                if (doctor.registered_at) {
                    const regDate = new Date(doctor.registered_at);
                    document.getElementById('doctorRegisteredAt').textContent = 
                        regDate.toLocaleDateString('ru-RU');
                }
            }
            
            // Обновляем приветствие на dashboard
            const welcomeElements = document.querySelectorAll('.text-muted');
            welcomeElements.forEach(element => {
                if (element.textContent.includes('Добро пожаловать')) {
                    element.textContent = `Добро пожаловать, Доктор ${doctor.last_name}`;
                }
            });
            
        } else {
            console.error('Profile load failed:', result.message);
            showNotification('Ошибка загрузки профиля', 'error');
        }
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
        // Не показываем уведомление об ошибке, чтобы не мешать пользователю
    }
}

function showNotification(message, type = 'info') {
    // Простая реализация уведомлений
    alert(`${type.toUpperCase()}: ${message}`);
}

// Проверяем, является ли страница защищенной (требует авторизации)
function isProtectedPage() {
    // Исключаем публичные страницы
    const publicPages = ['/', '/login', '/registration'];
    return !publicPages.includes(window.location.pathname);
}

// Обработчики для форм
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, current path:', window.location.pathname);
    
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
    
    // Загружаем данные профиля для ВСЕХ защищенных страниц
    if (isProtectedPage()) {
        console.log('Protected page detected, loading profile data...');
        loadProfileData();
    }
});