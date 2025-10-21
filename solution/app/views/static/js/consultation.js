document.addEventListener('DOMContentLoaded', function () {
    console.log('Consultation page loaded');

    // Элементы интерфейса
    const questionText = document.getElementById('questionText');
    const questionNumber = document.getElementById('questionNumber');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const answersList = document.getElementById('answersList');
    const diagnosisPreview = document.getElementById('diagnosisPreview');
    const previewDiagnosisText = document.getElementById('previewDiagnosisText');
    const btnCompleteConsultation = document.getElementById('btnCompleteConsultation');
    const btnBack = document.getElementById('btnBack');
    const btnCancel = document.getElementById('btnCancel');
    const toggleAnswers = document.getElementById('toggleAnswers');

    // Данные консультации
    const consultationId = document.getElementById('consultationId')?.value;
    const patientId = document.getElementById('patientId')?.value;

    console.log('Consultation ID:', consultationId);
    console.log('Patient ID:', patientId);

    if (!consultationId || !patientId) {
        console.error('Отсутствует ID консультации или пациента');
        return;
    }

    // Обработчики ответов
    document.querySelectorAll('.btn-answer').forEach(btn => {
        btn.addEventListener('click', function () {
            const answer = this.getAttribute('data-answer');
            console.log('Answer clicked:', answer);
            saveAnswer(answer);
        });
    });

    // Обработчики клавиатуры
    document.addEventListener('keydown', function (e) {
        if (e.key.toLowerCase() === 'y') {
            console.log('Keyboard Y pressed');
            saveAnswer('yes');
        } else if (e.key.toLowerCase() === 'n') {
            console.log('Keyboard N pressed');
            saveAnswer('no');
        }
    });

    // Завершение консультации
    btnCompleteConsultation?.addEventListener('click', completeConsultation);

    // Отмена консультации
    btnCancel?.addEventListener('click', cancelConsultation);

    // Переключение отображения ответов
    toggleAnswers?.addEventListener('click', function () {
        const answersContent = answersList.parentElement;
        const isHidden = answersContent.style.display === 'none';

        answersContent.style.display = isHidden ? 'block' : 'none';
        this.textContent = isHidden ? 'Свернуть' : 'Развернуть';
    });

    async function saveAnswer(answer) {
        console.log('=== SAVE ANSWER START ===');
        console.log('Saving answer:', answer, 'for consultation:', consultationId);

        // Показываем loading state
        document.querySelectorAll('.btn-answer').forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.6';
        });

        try {
            const response = await fetch('/api/consultation/save-answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consultation_id: parseInt(consultationId),
                    answer: answer
                })
            });

            const result = await response.json();
            console.log('Save answer response:', result);

            if (result.success) {
                updateInterface(result);
            } else {
                console.error('Error saving answer:', result.message);
                alert('Ошибка: ' + result.message);
            }
        } catch (error) {
            console.error('Ошибка при сохранении ответа:', error);
            alert('Ошибка при сохранении ответа');
        } finally {
            // Восстанавливаем кнопки
            document.querySelectorAll('.btn-answer').forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
            });
        }
        console.log('=== SAVE ANSWER COMPLETE ===');
    }

    function updateInterface(data) {
        console.log('Updating interface with data:', data);

        // Обновляем прогресс
        if (data.progress) {
            progressFill.style.width = data.progress.progress_percent + '%';
            progressText.textContent = `${Math.round(data.progress.progress_percent)}% завершено (${data.progress.questions_answered} вопросов)`;
        }

        // Обновляем номер вопроса
        if (data.progress) {
            questionNumber.textContent = `Вопрос ${data.progress.questions_answered + 1}`;
        }

        // Обновляем текст вопроса
        let newQuestionText = '';
        if (data.next_question && data.next_question.text) {
            newQuestionText = data.next_question.text;
        } else if (data.progress && data.progress.current_question) {
            newQuestionText = data.progress.current_question;
        }

        if (newQuestionText) {
            questionText.textContent = newQuestionText;
        }

        // Если достигли диагноза, показываем превью и блокируем кнопки
        if (data.next_question && data.next_question.is_final) {
            const diagnosis = data.diagnosis_candidate || data.next_question.text;
            showDiagnosisPreview(diagnosis);
            // Блокируем кнопки ответов
            document.querySelectorAll('.btn-answer').forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
            });
        } else if (data.diagnosis_candidate) {
            showDiagnosisPreview(data.diagnosis_candidate);
            // Блокируем кнопки ответов
            document.querySelectorAll('.btn-answer').forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
            });
        } else {
            hideDiagnosisPreview();
            // Разблокируем кнопки
            document.querySelectorAll('.btn-answer').forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
            });
        }

        // Обновляем историю ответов
        updateAnswersHistory();
    }

    function showDiagnosisPreview(diagnosis) {
        previewDiagnosisText.textContent = diagnosis;
        diagnosisPreview.style.display = 'block';
        console.log('Diagnosis preview shown:', diagnosis);

        // Прокручиваем к превью диагноза
        diagnosisPreview.scrollIntoView({ behavior: 'smooth' });
    }

    function hideDiagnosisPreview() {
        diagnosisPreview.style.display = 'none';
        console.log('Diagnosis preview hidden');
    }

    async function updateAnswersHistory() {
        try {
            console.log('Updating answers history');
            const response = await fetch(`/api/consultation/${consultationId}`);
            const result = await response.json();
            console.log('Answers history response:', result);

            if (result.success && result.consultation.sub_graph_find_diagnosis) {
                const answers = result.consultation.sub_graph_find_diagnosis.answers || {};
                renderAnswersHistory(answers);
            }
        } catch (error) {
            console.error('Ошибка при загрузке истории ответов:', error);
        }
    }

    function renderAnswersHistory(answers) {
        console.log('Rendering answers history:', answers);
        answersList.innerHTML = '';

        if (Object.keys(answers).length === 0) {
            answersList.innerHTML = `
                <div class="empty-state">
                    <p class="text-muted">Ответы пока отсутствуют</p>
                </div>
            `;
            return;
        }

        Object.entries(answers).forEach(([key, qa]) => {
            const answerItem = document.createElement('div');
            answerItem.className = `answer-item answer-${qa.answer}`;
            answerItem.innerHTML = `
                <span class="answer-icon">${qa.answer === 'yes' ? '✅' : '❌'}</span>
                <span class="answer-text">${qa.question} - ${qa.answer === 'yes' ? 'Да' : 'Нет'}</span>
            `;
            answersList.appendChild(answerItem);
        });
    }

    async function completeConsultation() {
        console.log('Completing consultation');
        try {
            const response = await fetch('/api/consultation/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consultation_id: parseInt(consultationId)
                })
            });

            const result = await response.json();
            console.log('Complete consultation response:', result);

            if (result.success) {
                // Перенаправляем на страницу результатов
                window.location.href = `/consultation/result?consultation_id=${consultationId}`;
            } else {
                alert('Ошибка: ' + result.message);
            }
        } catch (error) {
            console.error('Ошибка при завершении консультации:', error);
            alert('Ошибка при завершении консультации');
        }
    }

    async function cancelConsultation() {
        if (confirm('Вы уверены, что хотите отменить консультацию? Все данные будут потеряны.')) {
            // Здесь можно добавить API для отмены консультации
            window.location.href = '/consultation';
        }
    }

    // Инициализация интерфейса
    console.log('Initializing interface');
    updateAnswersHistory();
});

// Обработка завершения консультации
document.getElementById('btnCompleteConsultation').addEventListener('click', async function () {
    const consultationId = document.getElementById('consultationId').value;
    const diagnosisText = document.getElementById('previewDiagnosisText').textContent;

    try {
        const response = await fetch('/api/consultation/complete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                consultation_id: parseInt(consultationId),
                final_diagnosis: diagnosisText
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('Консультация успешно завершена!');
            // Перенаправляем на страницу результатов
            window.location.href = `/consultation/result?consultation_id=${consultationId}`;
        } else {
            alert('Ошибка при завершении консультации: ' + result.message);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при завершении консультации');
    }
});

// Обработка отмены консультации
document.getElementById('btnCancel').addEventListener('click', async function () {
    if (!confirm('Вы уверены, что хотите отменить консультацию? Все данные будут потеряны.')) {
        return;
    }

    const consultationId = document.getElementById('consultationId').value;

    try {
        const response = await fetch('/api/consultation/cancel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                consultation_id: parseInt(consultationId)
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('Консультация отменена');
            window.location.href = '/consultation';
        } else {
            alert('Ошибка при отмене консультации: ' + result.message);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при отмене консультации');
    }
});

// Автоматическое сохранение как черновика при уходе со страницы
window.addEventListener('beforeunload', function (e) {
    const consultationId = document.getElementById('consultationId').value;
    const diagnosisPreview = document.getElementById('diagnosisPreview');

    // Если консультация активна и не завершена, сохраняем как черновик
    if (consultationId && diagnosisPreview.style.display === 'none') {
        // Не блокируем уход, но пытаемся сохранить
        fetch('/api/consultation/save-draft', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                consultation_id: parseInt(consultationId)
            }),
            keepalive: true // Позволяет выполнить запрос даже при уходе со страницы
        }).catch(error => console.error('Ошибка автосохранения:', error));
    }
});

// Обработка сохранения как черновика
document.getElementById('btnSaveDraft').addEventListener('click', async function () {
    const consultationId = document.getElementById('consultationId').value;

    try {
        const response = await fetch('/api/consultation/save-draft', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                consultation_id: parseInt(consultationId)
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('Консультация сохранена как черновик. Вы можете продолжить позже.');
            window.location.href = '/consultation';
        } else {
            alert('Ошибка при сохранении черновика: ' + result.message);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при сохранении черновика');
    }
});