// Consultation process logic with decision graph
class ConsultationProcess {
    constructor() {
        this.consultationId = document.getElementById('consultationId')?.value;
        this.patientId = document.getElementById('patientId')?.value;
        this.isDiagnosisReached = false;
        this.init();
    }

    init() {
        if (!this.consultationId || !this.patientId) {
            return; // Нет активной консультации
        }
        
        this.bindEvents();
        this.setupKeyboardNavigation();
        this.loadConsultationData();
    }

    async loadConsultationData() {
        try {
            const response = await fetch(`/api/consultation/${this.consultationId}`);
            const result = await response.json();
            
            if (result.success) {
                this.updateUI(result.consultation, result.progress, result.current_question);
            }
        } catch (error) {
            console.error('Ошибка загрузки данных консультации:', error);
            this.showToast('Ошибка загрузки данных консультации', 'error');
        }
    }

    bindEvents() {
        // Answer buttons
        document.querySelectorAll('.btn-answer').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const answer = e.currentTarget.dataset.answer;
                this.handleAnswer(answer);
            });
        });

        // Back button
        const backBtn = document.getElementById('btnBack');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                this.showToast('Функция возврата находится в разработке', 'warning');
            });
        }

        // Cancel button
        const cancelBtn = document.getElementById('btnCancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.cancelConsultation();
            });
        }

        // Complete consultation button
        const completeBtn = document.getElementById('btnCompleteConsultation');
        if (completeBtn) {
            completeBtn.addEventListener('click', () => {
                this.completeConsultation();
            });
        }

        // Toggle answers
        const toggleBtn = document.getElementById('toggleAnswers');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.toggleAnswers();
            });
        }
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            if (!this.consultationId || this.isDiagnosisReached) return;
            
            switch(e.key.toLowerCase()) {
                case 'y':
                case 'н': // Русская раскладка
                    e.preventDefault();
                    this.handleAnswer('yes');
                    break;
                case 'n':
                case 'т': // Русская раскладка
                    e.preventDefault();
                    this.handleAnswer('no');
                    break;
                case 'escape':
                    this.cancelConsultation();
                    break;
            }
        });
    }

    async handleAnswer(answer) {
        if (this.isDiagnosisReached) return;
        
        // Add visual feedback
        this.showAnswerFeedback(answer);

        try {
            const response = await fetch('/api/consultation/save-answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consultation_id: parseInt(this.consultationId),
                    answer: answer
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('Ответ сохранен', 'success');
                
                // Обновляем UI
                this.updateUIAfterAnswer(result);
                
                // Проверяем, достигли ли диагноза
                if (result.diagnosis_candidate) {
                    this.showDiagnosisPreview(result.diagnosis_candidate);
                }
            } else {
                this.showToast('Ошибка сохранения ответа: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('Ошибка сохранения ответа:', error);
            this.showToast('Ошибка сохранения ответа', 'error');
        }
    }

    updateUI(consultation, progress, currentQuestion) {
        // Обновляем прогресс
        this.updateProgress(progress);
        
        // Обновляем текущий вопрос
        if (currentQuestion && currentQuestion.text) {
            document.getElementById('questionText').textContent = currentQuestion.text;
        }
        
        // Обновляем номер вопроса
        const questionNumber = document.getElementById('questionNumber');
        if (questionNumber && progress) {
            questionNumber.textContent = `Вопрос ${progress.questions_answered + 1}`;
        }
        
        // Обновляем историю ответов
        this.updateAnswersHistory(consultation.sub_graph_find_diagnosis?.answers);
    }

    updateUIAfterAnswer(result) {
        if (result.progress) {
            this.updateProgress(result.progress);
        }
        
        if (result.next_question) {
            document.getElementById('questionText').textContent = result.next_question.text;
            
            // Обновляем номер вопроса
            const questionNumber = document.getElementById('questionNumber');
            if (questionNumber && result.progress) {
                questionNumber.textContent = `Вопрос ${result.progress.questions_answered + 1}`;
            }
        }
        
        // Перезагружаем полные данные для обновления истории
        this.loadConsultationData();
    }

    updateProgress(progress) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        if (progressFill && progress.progress_percent !== undefined) {
            progressFill.style.width = `${progress.progress_percent}%`;
        }
        if (progressText) {
            progressText.textContent = `${Math.round(progress.progress_percent)}% завершено (${progress.questions_answered} вопросов)`;
        }
    }

    updateAnswersHistory(answers) {
        const answersList = document.getElementById('answersList');
        if (!answersList) return;

        answersList.innerHTML = '';
        
        if (!answers || Object.keys(answers).length === 0) {
            answersList.innerHTML = '<div class="empty-state"><p class="text-muted">Ответы пока отсутствуют</p></div>';
            return;
        }

        // Сортируем ответы по ключу (q1, q2, ...)
        const sortedAnswers = Object.entries(answers)
            .sort(([keyA], [keyB]) => {
                const numA = parseInt(keyA.replace('q', ''));
                const numB = parseInt(keyB.replace('q', ''));
                return numA - numB;
            });

        sortedAnswers.forEach(([key, qa]) => {
            const answerItem = document.createElement('div');
            answerItem.className = `answer-item answer-${qa.answer}`;
            answerItem.innerHTML = `
                <span class="answer-icon">${qa.answer === 'yes' ? '✅' : '❌'}</span>
                <span class="answer-text">${qa.question} - ${qa.answer === 'yes' ? 'Да' : 'Нет'}</span>
            `;
            answersList.appendChild(answerItem);
        });
    }

    showDiagnosisPreview(diagnosis) {
        this.isDiagnosisReached = true;
        
        const preview = document.getElementById('diagnosisPreview');
        const diagnosisText = document.getElementById('previewDiagnosisText');
        
        if (preview && diagnosisText) {
            diagnosisText.textContent = diagnosis;
            preview.style.display = 'block';
            
            // Прокручиваем к превью диагноза
            preview.scrollIntoView({ behavior: 'smooth' });
            
            this.showToast('Достигнут предварительный диагноз!', 'success');
        }
    }

    showAnswerFeedback(answer) {
        const buttons = document.querySelectorAll('.btn-answer');
        buttons.forEach(btn => {
            btn.style.transform = 'scale(0.95)';
            btn.style.opacity = '0.7';
        });

        const selectedBtn = document.querySelector(`.btn-answer[data-answer="${answer}"]`);
        if (selectedBtn) {
            selectedBtn.style.transform = 'scale(1.1)';
            selectedBtn.style.opacity = '1';
            
            // Сбрасываем стиль через 500ms
            setTimeout(() => {
                selectedBtn.style.transform = '';
                selectedBtn.style.opacity = '';
            }, 500);
        }
    }

    async completeConsultation() {
        try {
            const response = await fetch('/api/consultation/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    consultation_id: parseInt(this.consultationId)
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('Консультация завершена!', 'success');
                
                // Переходим на страницу результатов
                setTimeout(() => {
                    window.location.href = `/consultation/result?consultation_id=${this.consultationId}`;
                }, 1500);
            } else {
                this.showToast('Ошибка завершения консультации: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('Ошибка завершения консультации:', error);
            this.showToast('Ошибка завершения консультации', 'error');
        }
    }

    cancelConsultation() {
        if (confirm('Вы уверены, что хотите отменить консультацию? Все несохраненные данные будут потеряны.')) {
            window.location.href = '/dashboard';
        }
    }

    toggleAnswers() {
        const answersList = document.getElementById('answersList');
        const toggleBtn = document.getElementById('toggleAnswers');
        
        if (!answersList || !toggleBtn) return;
        
        if (answersList.style.display === 'none') {
            answersList.style.display = 'block';
            toggleBtn.textContent = 'Свернуть';
        } else {
            answersList.style.display = 'none';
            toggleBtn.textContent = 'Развернуть';
        }
    }

    showToast(message, type = 'info') {
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
            boxShadow: 'var(--shadow-md)',
            fontSize: '14px'
        });

        document.body.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ConsultationProcess();
});