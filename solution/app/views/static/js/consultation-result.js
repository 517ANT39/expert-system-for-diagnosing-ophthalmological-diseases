// Consultation result page functionality
class ConsultationResult {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadConsultationData();
    }

    bindEvents() {
        // Form submission
        const form = document.querySelector('.doctor-notes-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.completeConsultation();
            });
        }

        // Real-time saving
        const inputs = document.querySelectorAll('#finalDiagnosis, #doctorNotes');
        inputs.forEach(input => {
            input.addEventListener('input', this.debounce(() => {
                this.saveDraft();
            }, 1000));
        });
    }

    loadConsultationData() {
        // In a real app, this would load data from the server
        const consultationData = {
            patient: {
                name: "Петров Иван Сергеевич",
                birthDate: "15.03.1985",
                gender: "Мужской"
            },
            diagnosis: {
                primary: "Острый конъюнктивит",
                confidence: 85,
                explanation: "Диагноз основан на выявленных симптомах...",
                symptoms: [
                    { name: "Покраснение глаза", present: true },
                    { name: "Слезотечение", present: true },
                    { name: "Боль в глазу", present: true },
                    { name: "Светобоязнь", present: false },
                    { name: "Выделения", present: false }
                ]
            },
            recommendations: {
                medication: [
                    "Антибактериальные капли: Ципрофлоксацин 0.3%",
                    "Противовоспалительные капли: Диклофенак 0.1%"
                ],
                general: [
                    "Избегать трения глаз",
                    "Частое мытье рук",
                    "Использование отдельного полотенца"
                ],
                followUp: [
                    "Повторный осмотр через 3 дня",
                    "Обратиться немедленно при ухудшении"
                ]
            }
        };

        this.displayData(consultationData);
    }

    displayData(data) {
        // Display patient info
        this.updateElement('.patient-details', `
            <div class="detail-item">
                <strong>ФИО:</strong> ${data.patient.name}
            </div>
            <div class="detail-item">
                <strong>Дата рождения:</strong> ${data.patient.birthDate}
            </div>
            <div class="detail-item">
                <strong>Пол:</strong> ${data.patient.gender}
            </div>
            <div class="detail-item">
                <strong>Дата консультации:</strong> ${new Date().toLocaleDateString('ru-RU')}
            </div>
        `);

        // Display diagnosis
        this.updateElement('.primary-diagnosis h3', data.diagnosis.primary);
        this.updateElement('.confidence-badge', `Уверенность: ${data.diagnosis.confidence}%`);

        // Display symptoms evidence
        const symptomsHTML = data.diagnosis.symptoms.map(symptom => `
            <li class="evidence-${symptom.present ? 'positive' : 'negative'}">
                ${symptom.present ? '✅' : '❌'} ${symptom.name}
            </li>
        `).join('');

        this.updateElement('.symptoms-evidence', symptomsHTML);
    }

    updateElement(selector, content) {
        const element = document.querySelector(selector);
        if (element) {
            element.innerHTML = content;
        }
    }

    saveDraft() {
        const formData = this.getFormData();
        
        // Save to localStorage (in real app - send to server)
        localStorage.setItem('consultation_draft', JSON.stringify(formData));
        
        this.showToast('Черновик сохранен', 'success');
    }

    async completeConsultation() {
        const formData = this.getFormData();
        
        // Validate form
        if (!formData.finalDiagnosis.trim()) {
            this.showToast('Пожалуйста, укажите окончательный диагноз', 'warning');
            return;
        }

        try {
            // Simulate API call
            await this.simulateAPICall();
            
            // Clear draft
            localStorage.removeItem('consultation_draft');
            
            this.showToast('Консультация успешно завершена', 'success');
            
            // Redirect to dashboard after delay
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 2000);
            
        } catch (error) {
            this.showToast('Ошибка при сохранении консультации', 'error');
        }
    }

    getFormData() {
        return {
            finalDiagnosis: document.getElementById('finalDiagnosis').value,
            doctorNotes: document.getElementById('doctorNotes').value,
            timestamp: new Date().toISOString()
        };
    }

    simulateAPICall() {
        return new Promise((resolve) => {
            setTimeout(resolve, 1500);
        });
    }

    showToast(message, type = 'info') {
        // Reuse toast functionality from consultation.js
        if (typeof ConsultationProcess !== 'undefined') {
            new ConsultationProcess().showToast(message, type);
        } else {
            // Fallback simple toast
            alert(message);
        }
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
}

// Export to PDF functionality
function exportToPDF() {
    // In a real app, this would generate an actual PDF
    const patientName = "Петров Иван Сергеевич";
    const diagnosis = document.getElementById('finalDiagnosis').value || "Острый конъюнктивит";
    
    alert(`Генерация PDF для пациента: ${patientName}\nДиагноз: ${diagnosis}\n\nВ реальной системе здесь будет создан PDF документ с полными результатами консультации.`);
    
    // Simulate PDF download
    ConsultationResult.prototype.showToast('PDF документ готов к скачиванию', 'success');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ConsultationResult();
});

// Load draft if exists
document.addEventListener('DOMContentLoaded', () => {
    const draft = localStorage.getItem('consultation_draft');
    if (draft) {
        const formData = JSON.parse(draft);
        document.getElementById('finalDiagnosis').value = formData.finalDiagnosis || '';
        document.getElementById('doctorNotes').value = formData.doctorNotes || '';
    }
});