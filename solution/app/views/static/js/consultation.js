// Consultation process logic
class ConsultationProcess {
    constructor() {
        this.currentQuestion = 1;
        this.totalQuestions = 12;
        this.symptoms = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupKeyboardNavigation();
        this.updateProgress();
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
                this.goToPreviousQuestion();
            });
        }

        // Cancel button
        const cancelBtn = document.getElementById('btnCancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.cancelConsultation();
            });
        }

        // Toggle symptoms
        const toggleBtn = document.getElementById('toggleSymptoms');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.toggleSymptoms();
            });
        }
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Prevent default behavior only for our shortcuts
            if (e.key === '1' || e.key === '2' || e.key === ' ') {
                e.preventDefault();
            }

            switch(e.key) {
                case '1':
                case ' ':
                    this.handleAnswer('yes');
                    break;
                case '2':
                    this.handleAnswer('no');
                    break;
                case 'Escape':
                    this.cancelConsultation();
                    break;
                case 'Backspace':
                    this.goToPreviousQuestion();
                    break;
            }
        });
    }

    handleAnswer(answer) {
        // Add visual feedback
        this.showAnswerFeedback(answer);

        // Simulate API call delay
        setTimeout(() => {
            this.symptoms.push({
                question: this.currentQuestion,
                answer: answer,
                timestamp: new Date()
            });

            this.currentQuestion++;
            this.updateProgress();

            if (this.currentQuestion > this.totalQuestions) {
                this.completeConsultation();
            } else {
                this.updateQuestion();
            }
        }, 500);
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
        }
    }

    updateProgress() {
        const progress = (this.currentQuestion / this.totalQuestions) * 100;
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        const questionNumber = document.querySelector('.question-number');

        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}% завершено`;
        }
        if (questionNumber) {
            questionNumber.textContent = `Вопрос ${this.currentQuestion} из ${this.totalQuestions}`;
        }
    }

    updateQuestion() {
        // In a real app, this would fetch the next question from the server
        const questions = [
            "❓ Пациент жалуется на боль в глазу?",
            "❓ Есть ли покраснение глаза?",
            "❓ Наблюдаются ли выделения из глаза?",
            "❓ Есть ли слезотечение?",
            "❓ Беспокоит ли светобоязнь?",
            "❓ Отмечается ли ухудшение зрения?",
            "❓ Есть ли ощущение инородного тела?",
            "❓ Беспокоит ли зуд в области глаз?",
            "❓ Наблюдается ли отечность век?",
            "❓ Есть ли головная боль?",
            "❓ Отмечается ли тошнота?",
            "❓ Были ли травмы глаза в последнее время?"
        ];

        const questionText = document.querySelector('.question-text');
        if (questionText && questions[this.currentQuestion - 1]) {
            questionText.textContent = questions[this.currentQuestion - 1];
        }

        // Reset button styles
        document.querySelectorAll('.btn-answer').forEach(btn => {
            btn.style.transform = '';
            btn.style.opacity = '';
        });
    }

    goToPreviousQuestion() {
        if (this.currentQuestion > 1) {
            this.currentQuestion--;
            this.symptoms.pop(); // Remove last answer
            this.updateProgress();
            this.updateQuestion();
        } else {
            this.showToast('Это первый вопрос', 'warning');
        }
    }

    cancelConsultation() {
        if (confirm('Вы уверены, что хотите отменить консультацию? Все несохраненные данные будут потеряны.')) {
            // Используем Flask route для dashboard
            window.location.href = '/dashboard';
        }
    }

    completeConsultation() {
        // Используем Flask route для consultation result
        window.location.href = '/consultation/result';
    }

    toggleSymptoms() {
        const symptomsList = document.getElementById('symptomsList');
        const toggleBtn = document.getElementById('toggleSymptoms');
        
        if (!symptomsList || !toggleBtn) return;
        
        if (symptomsList.style.display === 'none') {
            symptomsList.style.display = 'grid';
            toggleBtn.textContent = 'Свернуть';
        } else {
            symptomsList.style.display = 'none';
            toggleBtn.textContent = 'Развернуть';
        }
    }

    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'warning' ? '#FEF3C7' : '#DBEAFE',
            color: type === 'warning' ? '#D97706' : '#1E40AF',
            padding: '1rem 1.5rem',
            borderRadius: 'var(--border-radius)',
            border: `1px solid ${type === 'warning' ? '#FCD34D' : '#93C5FD'}`,
            zIndex: '1000',
            boxShadow: 'var(--shadow-md)'
        });

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ConsultationProcess();
});

// Utility functions
const ConsultationUtils = {
    // Format symptoms for display
    formatSymptom(symptom, answer) {
        return {
            text: `${symptom} - ${answer ? 'Да' : 'Нет'}`,
            type: answer ? 'positive' : 'negative'
        };
    },

    // Calculate diagnosis probability (simplified)
    calculateProbability(symptoms) {
        // This would be replaced with actual graph traversal logic
        const positiveSymptoms = symptoms.filter(s => s.answer === 'yes').length;
        return (positiveSymptoms / symptoms.length) * 100;
    }
};