document.addEventListener('DOMContentLoaded', function () {
    console.log('patient-new.js loaded - ИСПРАВЛЕННАЯ ВЕРСИЯ');
    
    const form = document.getElementById('patientForm');
    const saveButton = form.querySelector('button[type="submit"]');

    // Функция для получения выбранного пола
    function getSelectedGender() {
        const selectedGender = document.querySelector('input[name="gender"]:checked');
        console.log('Найден выбранный пол:', selectedGender ? selectedGender.value : 'не выбран');
        return selectedGender ? selectedGender.value : null;
    }

    // Добавляем отладку для радиокнопок
    document.querySelectorAll('input[name="gender"]').forEach(radio => {
        radio.addEventListener('change', function() {
            console.log('Изменен пол на:', this.value);
        });
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        console.log('=== НАЧАЛО ОБРАБОТКИ ФОРМЫ ===');

        // Получаем пол ДО создания formData
        const selectedGender = getSelectedGender();
        console.log('Выбранный пол перед отправкой:', selectedGender);

        if (!selectedGender) {
            alert('Пожалуйста, выберите пол пациента');
            return;
        }

        // Собираем данные формы
        const formData = {
            last_name: document.getElementById('lastName').value.trim(),
            first_name: document.getElementById('firstName').value.trim(),
            middle_name: document.getElementById('middleName').value.trim(),
            birthday: document.getElementById('birthDate').value,
            sex: selectedGender, // Используем уже полученное значение
            phone: document.getElementById('phone').value.trim(),
            email: document.getElementById('email').value.trim(),
            address: document.getElementById('address').value.trim(),
            allergies: document.getElementById('allergies').value.trim(),
            chronic_diseases: document.getElementById('chronicDiseases').value.trim(),
            current_medications: document.getElementById('currentMedications').value.trim(),
            family_anamnes: document.getElementById('familyHistory').value.trim(),
            notes: document.getElementById('notes').value.trim()
        };

        console.log('=== ДАННЫЕ ДЛЯ ОТПРАВКИ ===');
        console.log('Пол (sex):', formData.sex);
        console.log('Тип пола:', typeof formData.sex);
        console.log('Все данные:', JSON.stringify(formData, null, 2));

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

            console.log('Статус ответа:', response.status);
            console.log('URL ответа:', response.url);

            const result = await response.json();
            console.log('Результат от сервера:', result);

            if (result.success) {
                console.log('Пациент успешно создан с ID:', result.patient?.id);
                alert('Пациент успешно сохранен!');
                window.location.href = '/patients';
            } else {
                console.error('Ошибка от сервера:', result.message);
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
    document.getElementById('saveDraftBtn').addEventListener('click', function () {
        alert('Функция сохранения черновика в разработке');
    });

    // Установка максимальной даты рождения (сегодня)
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('birthDate').setAttribute('max', today);

    // Дополнительная отладка при загрузке
    console.log('Все радиокнопки пола:', document.querySelectorAll('input[name="gender"]').length);
});