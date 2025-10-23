document.addEventListener('DOMContentLoaded', function () {
    console.log('Consultation page loaded');

    // Элементы интерфейса
    const questionText = document.getElementById('questionText');
    const questionNumber = document.getElementById('questionNumber');
    const answersList = document.getElementById('answersList');
    const diagnosisPreview = document.getElementById('diagnosisPreview');
    const questionView = document.getElementById('questionView');
    const previewDiagnosisText = document.getElementById('previewDiagnosisText');
    const btnBack = document.getElementById('btnBack');
    const btnCancel = document.getElementById('btnCancel');
    const toggleAnswers = document.getElementById('toggleAnswers');
    const btnSaveDraft = document.getElementById('btnSaveDraft');

    // Новые элементы для рекомендаций
    const doctorRecommendationsCard = document.getElementById('doctorRecommendationsCard');
    const doctorNotes = document.getElementById('doctorNotes');
    const confirmRecommendationsBtn = document.getElementById('confirmRecommendationsBtn');
    const recommendationsStatus = document.getElementById('recommendationsStatus');
    const recommendationsConfirmed = document.getElementById('recommendationsConfirmed');

    // Секция завершения консультации
    const consultationCompletedSection = document.getElementById('consultationCompletedSection');
    const viewResultsBtn = document.getElementById('viewResultsBtn');
    const exportPdfBtn = document.getElementById('exportPdfBtn');

    // Данные консультации
    const consultationId = document.getElementById('consultationId')?.value;
    const patientId = document.getElementById('patientId')?.value;

    console.log('Consultation ID:', consultationId);
    console.log('Patient ID:', patientId);

    if (!consultationId || !patientId) {
        console.error('Отсутствует ID консультации или пациента');
        return;
    }

    // Инициализация - скрываем карточку рекомендаций и секцию завершения
    hideRecommendationsCard();
    hideCompletionSection();

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

    // Отмена консультации
    if (btnCancel) {
        btnCancel.addEventListener('click', cancelConsultation);
    }

    // Переключение отображения ответов
    if (toggleAnswers) {
        toggleAnswers.addEventListener('click', function () {
            const answersContent = answersList.parentElement;
            const isHidden = answersContent.style.display === 'none';

            answersContent.style.display = isHidden ? 'block' : 'none';
            this.textContent = isHidden ? 'Свернуть' : 'Развернуть';
        });
    }

    // Обработчик сохранения рекомендаций (необязательных)
    if (confirmRecommendationsBtn) {
        confirmRecommendationsBtn.addEventListener('click', confirmRecommendations);
    }

    // Обработчик экспорта PDF
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', function () {
            if (consultationId) {
                window.open(`/consultation/${consultationId}/export-pdf`, '_blank');
            }
        });
    }

    // Валидация поля рекомендаций (необязательное)
    if (doctorNotes) {
        doctorNotes.addEventListener('input', function () {
            const hasText = this.value.trim().length > 0;

            if (recommendationsStatus) {
                if (hasText) {
                    recommendationsStatus.textContent = 'Готово к сохранению';
                    recommendationsStatus.className = 'recommendations-status status-confirmed';
                } else {
                    recommendationsStatus.textContent = 'Рекомендации можно добавить по желанию';
                    recommendationsStatus.className = 'recommendations-status';
                }
            }
        });
    }

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

        // Обновляем текст вопроса
        let newQuestionText = '';
        if (data.next_question && data.next_question.text) {
            newQuestionText = data.next_question.text;
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

            hideQuestionView();
            if (btnSaveDraft) btnSaveDraft.style.display = 'none';
            if (btnCancel) btnCancel.style.display = 'none';

            // ПОКАЗЫВАЕМ карточку рекомендаций
            showRecommendationsCard();

            // Автоматически завершаем консультацию (только статус, без рекомендаций)
            completeConsultationAutomatically(diagnosis);

        } else if (data.diagnosis_candidate) {
            showDiagnosisPreview(data.diagnosis_candidate);
            // Блокируем кнопки ответов
            document.querySelectorAll('.btn-answer').forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
            });
            // ПОКАЗЫВАЕМ карточку рекомендаций
            showRecommendationsCard();
        } else {
            hideDiagnosisPreview();
            hideRecommendationsCard();
            hideCompletionSection();
            // Разблокируем кнопки
            document.querySelectorAll('.btn-answer').forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
            });
        }

        // Обновляем историю ответов
        updateAnswersHistory();
    }

    async function completeConsultationAutomatically(diagnosis) {
        console.log('Automatically completing consultation with diagnosis:', diagnosis);

        try {
            // Автоматически завершаем консультацию БЕЗ рекомендаций
            const response = await fetch('/api/consultation/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consultation_id: parseInt(consultationId),
                    final_diagnosis: diagnosis,
                    notes: '' // Пустые рекомендации при автоматическом завершении
                })
            });

            const result = await response.json();
            console.log('Auto-complete consultation response:', result);

            if (result.success) {
                // Обновляем ссылку на результаты
                if (viewResultsBtn) {
                    viewResultsBtn.href = `/consultation/result?consultation_id=${consultationId}`;
                }

                console.log('Consultation automatically completed with status: completed');

                // НЕ показываем секцию завершения сразу, ждем рекомендаций врача
                // showCompletionSection();

            } else {
                console.error('Error auto-completing consultation:', result.message);
            }
        } catch (error) {
            console.error('Ошибка при автоматическом завершении консультации:', error);
        }
    }

    function showDiagnosisPreview(diagnosis) {
        if (previewDiagnosisText) {
            previewDiagnosisText.textContent = diagnosis;
        }
        if (diagnosisPreview) {
            diagnosisPreview.style.display = 'block';
        }

        // Сбрасываем форму рекомендаций
        resetRecommendationsForm();

        console.log('Diagnosis preview shown:', diagnosis);

        // Прокручиваем к превью диагноза
        if (diagnosisPreview) {
            diagnosisPreview.scrollIntoView({ behavior: 'smooth' });
        }
    }

    function hideDiagnosisPreview() {
        if (diagnosisPreview) {
            diagnosisPreview.style.display = 'none';
        }
        console.log('Diagnosis preview hidden');
    }

    function showRecommendationsCard() {
        if (doctorRecommendationsCard) {
            doctorRecommendationsCard.style.display = 'block';
            console.log('Recommendations card shown');
        }
    }

    function hideRecommendationsCard() {
        if (doctorRecommendationsCard) {
            doctorRecommendationsCard.style.display = 'none';
            console.log('Recommendations card hidden');
        }
    }

    function showCompletionSection() {
        if (consultationCompletedSection) {
            consultationCompletedSection.style.display = 'block';
            console.log('Completion section shown');

            // Прокручиваем к секции завершения
            consultationCompletedSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    function hideCompletionSection() {
        if (consultationCompletedSection) {
            consultationCompletedSection.style.display = 'none';
            console.log('Completion section hidden');
        }
    }

    function hideQuestionView() {
        if (questionView) {
            questionView.style.display = 'none';
        }
        console.log('question view hidden');
    }

    function resetRecommendationsForm() {
        if (doctorNotes) {
            doctorNotes.value = '';
            doctorNotes.disabled = false;
        }
        if (confirmRecommendationsBtn) {
            confirmRecommendationsBtn.disabled = false;
            confirmRecommendationsBtn.textContent = 'Сохранить рекомендации';
            confirmRecommendationsBtn.style.display = 'block';
        }
        if (recommendationsStatus) {
            recommendationsStatus.textContent = 'Рекомендации можно добавить по желанию';
            recommendationsStatus.className = 'recommendations-status';
        }
        if (recommendationsConfirmed) {
            recommendationsConfirmed.style.display = 'none';
        }
    }

    async function confirmRecommendations() {
        console.log('Confirm recommendations button clicked');

        if (!doctorNotes) {
            console.error('Doctor notes element not found');
            return;
        }

        const notes = doctorNotes.value.trim();
        const diagnosisText = document.getElementById('previewDiagnosisText').textContent;

        console.log('Saving recommendations:', notes);
        console.log('Final diagnosis:', diagnosisText);

        // Показываем загрузку
        if (confirmRecommendationsBtn) {
            confirmRecommendationsBtn.disabled = true;
            confirmRecommendationsBtn.textContent = 'Сохранение...';
        }
        if (recommendationsStatus) {
            recommendationsStatus.textContent = 'Сохранение рекомендаций...';
        }

        try {
            // Сохраняем рекомендации через API завершения консультации
            const response = await fetch('/api/consultation/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consultation_id: parseInt(consultationId),
                    final_diagnosis: diagnosisText,
                    notes: notes
                })
            });

            const result = await response.json();
            console.log('Complete consultation response:', result);

            if (result.success) {
                // Блокируем форму
                if (doctorNotes) {
                    doctorNotes.disabled = true;
                }
                if (confirmRecommendationsBtn) {
                    confirmRecommendationsBtn.style.display = 'none';
                }

                // Показываем секцию подтверждения
                if (recommendationsConfirmed) {
                    recommendationsConfirmed.style.display = 'block';
                }
                if (recommendationsStatus) {
                    recommendationsStatus.textContent = '✅ Рекомендации сохранены';
                    recommendationsStatus.className = 'recommendations-status status-confirmed';
                }

                // Показываем секцию завершения консультации
                showCompletionSection();

                // Обновляем ссылку на результаты
                if (viewResultsBtn) {
                    viewResultsBtn.href = `/consultation/result?consultation_id=${consultationId}`;
                }

                console.log('Recommendations confirmed and consultation completed:', notes);

            } else {
                throw new Error(result.message);
            }

        } catch (error) {
            console.error('Ошибка при сохранении рекомендаций:', error);
            alert('Ошибка при сохранении рекомендаций: ' + error.message);

            // Восстанавливаем кнопку
            if (confirmRecommendationsBtn) {
                confirmRecommendationsBtn.disabled = false;
                confirmRecommendationsBtn.textContent = 'Сохранить рекомендации';
            }
            if (recommendationsStatus) {
                recommendationsStatus.textContent = 'Ошибка при сохранении';
            }
        }
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
        if (!answersList) return;

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

        // Получаем рекомендации (могут быть пустыми)
        const notes = sessionStorage.getItem(`consultation_${consultationId}_notes`) || '';
        const diagnosisText = document.getElementById('previewDiagnosisText').textContent;

        try {
            const response = await fetch('/api/consultation/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consultation_id: parseInt(consultationId),
                    final_diagnosis: diagnosisText,
                    notes: notes
                })
            });

            const result = await response.json();
            console.log('Complete consultation response:', result);

            if (result.success) {
                // Очищаем временные данные
                sessionStorage.removeItem(`consultation_${consultationId}_notes`);
                sessionStorage.removeItem(`consultation_${consultationId}_notes_confirmed`);

                alert('Консультация успешно завершена!');
                // Перенаправляем на страницу результатов
                window.location.href = `/consultation/result?consultation_id=${consultationId}`;
            } else {
                alert('Ошибка при завершении консультации: ' + result.message);
            }
        } catch (error) {
            console.error('Ошибка при завершении консультации:', error);
            alert('Ошибка при завершении консультации');
        }
    }

    async function cancelConsultation() {
        if (confirm('Вы уверены, что хотите отменить консультацию? Все данные будут потеряны.')) {
            // Очищаем временные данные
            sessionStorage.removeItem(`consultation_${consultationId}_notes`);
            sessionStorage.removeItem(`consultation_${consultationId}_notes_confirmed`);

            // Здесь можно добавить API для отмены консультации
            window.location.href = '/consultation';
        }
    }

    // Инициализация интерфейса
    console.log('Initializing interface');
    updateAnswersHistory();
});

// Обработка отмены консультации
document.addEventListener('DOMContentLoaded', function () {
    const btnCancel = document.getElementById('btnCancel');
    if (btnCancel) {
        btnCancel.addEventListener('click', async function () {
            if (!confirm('Вы уверены, что хотите отменить консультацию? Все данные будут потеряны.')) {
                return;
            }

            const consultationId = document.getElementById('consultationId')?.value;
            if (!consultationId) return;

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
    }
});

// Автоматическое сохранение как черновика при уходе со страницы
window.addEventListener('beforeunload', function (e) {
    const consultationId = document.getElementById('consultationId')?.value;
    const diagnosisPreview = document.getElementById('diagnosisPreview');

    // Если консультация активна и не завершена, сохраняем как черновик
    if (consultationId && diagnosisPreview && diagnosisPreview.style.display === 'none') {
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
document.addEventListener('DOMContentLoaded', function () {
    const btnSaveDraft = document.getElementById('btnSaveDraft');
    if (btnSaveDraft) {
        btnSaveDraft.addEventListener('click', async function () {
            const consultationId = document.getElementById('consultationId')?.value;
            if (!consultationId) return;

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
    }
});