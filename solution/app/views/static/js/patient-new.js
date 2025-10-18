document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('patientForm');
    const saveButton = form.querySelector('button[type="submit"]');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        console.log('Форма отправляется...');
        
        // Собираем данные формы
        const genderInput = document.querySelector('input[name="gender"]:checked');
        if (!genderInput) {
            alert('Пожалуйста, выберите пол пациента');
            return;
        }
        
        const formData = {
            last_name: document.getElementById('lastName').value.trim(),
            first_name: document.getElementById('firstName').value.trim(),
            middle_name: document.getElementById('middleName').value.trim(),
            birthday: document.getElementById('birthDate').value,
            sex: genderInput.value,
            phone: document.getElementById('phone').value.trim(),
            email: document.getElementById('email').value.trim(),
            address: document.getElementById('address').value.trim(),
            allergies: document.getElementById('allergies').value.trim(),
            chronic_diseases: document.getElementById('chronicDiseases').value.trim(),
            current_medications: document.getElementById('currentMedications').value.trim(),
            family_anamnes: document.getElementById('familyHistory').value.trim(),
            notes: document.getElementById('notes').value.trim()
        };
        
        console.log('Собранные данные:', formData);
        
        // Валидация обязательных полей
        if (!formData.last_name || !formData.first_name || !formData.birthday || !formData.sex) {
            alert('Пожалуйста, заполните все обязательные поля (отмечены *)');
            return;
        }
        
        // Блокируем кнопку
        saveButton.disabled = true;
        saveButton.textContent = 'Сохранение...';
        
        try {
            console.log('Отправка запроса на /api/patients...');
            
            const response = await fetch('/api/patients', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            console.log('Получен ответ:', response.status);
            
            const result = await response.json();
            console.log('Результат:', result);
            
            if (result.success) {
                alert('Пациент успешно сохранен!');
                window.location.href = '/patients'; // Перенаправляем к списку пациентов
            } else {
                alert('Ошибка при сохранении: ' + result.message);
            }
        } catch (error) {
            console.error('Ошибка сети:', error);
            alert('Ошибка сети: ' + error.message);
        } finally {
            // Разблокируем кнопку
            saveButton.disabled = false;
            saveButton.textContent = '✅ Сохранить пациента';
        }
    });
    
    // Обработчик для кнопки "Сохранить черновик"
    document.getElementById('saveDraftBtn').addEventListener('click', function() {
        alert('Функция сохранения черновика в разработке');
        // Можно реализовать сохранение в localStorage
    });
    
    // Установка максимальной даты рождения (сегодня)
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('birthDate').setAttribute('max', today);
});