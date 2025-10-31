// Patient history functionality
class PatientHistory {
    constructor() {
        this.currentView = 'timeline';
        this.patientId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadPatientData();
        this.setupViewToggle();
    }

    bindEvents() {
        // Export buttons - только для завершенных консультаций
        document.addEventListener('click', (e) => {
            if (e.target.closest('.export-btn')) {
                const consultationId = e.target.closest('.export-btn').getAttribute('onclick').match(/\d+/)[0];
                this.exportConsultation(consultationId);
            }
        });

        // View toggle
        const viewButtons = document.querySelectorAll('[data-view]');
        viewButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchView(e.target.dataset.view);
            });
        });

        // Load patient from URL parameters
        this.loadFromURL();
    }

    loadFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        this.patientId = urlParams.get('patientId') || '001';
        
        // In a real app, load patient data based on ID
        this.updatePatientHeader(this.patientId);
    }

    loadPatientData() {
        // Simulate loading patient data
        const patientData = {
            '001': {
                name: 'Петров Иван Сергеевич',
                birthDate: '15.03.1985',
                gender: 'Мужской',
                email: 'ivan.petrov@email.com',
                phone: '+7 (912) 345-67-89',
                allergies: 'Пенициллин',
                chronicDiseases: 'Гипертония',
                currentMedications: 'Лозартан 50мг ежедневно'
            }
        };

        this.patientData = patientData[this.patientId] || patientData['001'];
    }

    updatePatientHeader(patientId) {
        // Update patient information in the header
        const patientName = document.querySelector('.patient-details h1');
        const patientMeta = document.querySelector('.patient-meta');
        
        if (patientName) {
            patientName.textContent = this.patientData.name;
        }
        
        // Update other patient details as needed
    }

    setupViewToggle() {
        // Set initial view
        this.switchView('timeline');
    }

    switchView(view) {
        this.currentView = view;
        
        // Update active button
        document.querySelectorAll('[data-view]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        
        // Show/hide views
        const timelineView = document.getElementById('timelineView');
        const listView = document.getElementById('listView');
        
        if (timelineView && listView) {
            if (view === 'timeline') {
                timelineView.style.display = 'block';
                listView.style.display = 'none';
            } else {
                timelineView.style.display = 'none';
                listView.style.display = 'block';
            }
        }
    }

    exportConsultation(consultationId) {
        // Проверяем статус консультации перед экспортом
        fetch(`/api/consultation/${consultationId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.consultation.status === 'completed') {
                    this.showToast('Генерация PDF документа...', 'info');
                    window.open(`/consultation/${consultationId}/export-pdf`, '_blank');
                } else {
                    this.showToast('Экспорт доступен только для завершенных консультаций', 'warning');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.showToast('Ошибка при проверке статуса консультации', 'error');
            });
    }

    generatePDF(consultationId) {
        // This would integrate with a PDF generation library
        // For example: jsPDF, pdfmake, etc.
        console.log('Generating PDF for consultation:', consultationId);
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
            boxShadow: 'var(--shadow-md)'
        });

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // Search and filter functionality
    searchConsultations(query) {
        const consultations = document.querySelectorAll('.timeline-item, .consultations-list tbody tr');
        
        consultations.forEach(consultation => {
            const text = consultation.textContent.toLowerCase();
            const isVisible = text.includes(query.toLowerCase());
            consultation.style.display = isVisible ? 'flex' : 'none';
            
            if (consultation.tagName === 'TR') {
                consultation.style.display = isVisible ? 'table-row' : 'none';
            }
        });
    }

    // Statistics calculation
    calculateStatistics() {
        const consultations = document.querySelectorAll('.timeline-item');
        const totalConsultations = consultations.length;
        
        // Calculate completed consultations
        const completedConsultations = Array.from(consultations).filter(consultation => {
            return consultation.querySelector('.status-completed') !== null;
        }).length;
        
        return {
            totalConsultations,
            completedConsultations
        };
    }
}

// Global function for export
function exportConsultation(consultationId) {
    const patientHistory = new PatientHistory();
    patientHistory.exportConsultation(consultationId);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PatientHistory();
});

// Add search functionality if needed
function setupConsultationSearch() {
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'Поиск по консультациям...';
    searchInput.className = 'form-control';
    searchInput.style.marginBottom = '1rem';
    
    searchInput.addEventListener('input', (e) => {
        const patientHistory = new PatientHistory();
        patientHistory.searchConsultations(e.target.value);
    });
    
    const cardHeader = document.querySelector('.card-header');
    if (cardHeader) {
        cardHeader.appendChild(searchInput);
    }
}