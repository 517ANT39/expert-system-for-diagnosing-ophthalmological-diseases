// Patient form functionality
class PatientForm {
    constructor() {
        this.form = document.getElementById('patientForm');
        this.isEditing = false;
        this.patientId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupValidation();
        this.checkEditMode();
        this.setMaxDate();
    }

    bindEvents() {
        // Form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });
        }

        // Save draft button
        const saveDraftBtn = document.getElementById('saveDraftBtn');
        if (saveDraftBtn) {
            saveDraftBtn.addEventListener('click', () => {
                this.saveDraft();
            });
        }

        // Phone input formatting
        const phoneInput = document.getElementById('phone');
        if (phoneInput) {
            phoneInput.addEventListener('input', (e) => {
                this.formatPhoneNumber(e.target);
            });
        }

        // Real-time validation
        const requiredFields = this.form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            field.addEventListener('blur', () => {
                this.validateField(field);
            });
        });

        // Load draft on page load
        this.loadDraft();
    }

    setupValidation() {
        // Add custom validation methods
        this.addEmailValidation();
        this.addBirthDateValidation();
    }

    addEmailValidation() {
        const emailInput = document.getElementById('email');
        if (emailInput) {
            emailInput.addEventListener('input', (e) => {
                const email = e.target.value;
                if (email && !this.isValidEmail(email)) {
                    this.showFieldError(emailInput, 'Введите корректный email адрес');
                } else {
                    this.clearFieldError(emailInput);
                }
            });
        }
    }

    addBirthDateValidation() {
        const birthDateInput = document.getElementById('birthDate');
        if (birthDateInput) {
            birthDateInput.addEventListener('change', (e) => {
                const birthDate = new Date(e.target.value);
                const today = new Date();
                const minDate = new Date();
                minDate.setFullYear(today.getFullYear() - 150); // 150 years ago

                if (birthDate > today) {
                    this.showFieldError(birthDateInput, 'Дата рождения не может быть в будущем');
                } else if (birthDate < minDate) {
                    this.showFieldError(birthDateInput, 'Проверьте дату рождения');
                } else {
                    this.clearFieldError(birthDateInput);
                }
            });
        }
    }

    setMaxDate() {
        const birthDateInput = document.getElementById('birthDate');
        if (birthDateInput) {
            const today = new Date().toISOString().split('T')[0];
            birthDateInput.setAttribute('max', today);
        }
    }

    checkEditMode() {
        // Check if we're editing an existing patient
        const urlParams = new URLSearchParams(window.location.search);
        const editId = urlParams.get('edit');
        
        if (editId) {
            this.isEditing = true;
            this.patientId = editId;
            this.loadPatientData(editId);
            this.updateUIForEdit();
        }
    }

    updateUIForEdit() {
        const pageTitle = document.querySelector('h1');
        const pageSubtitle = document.querySelector('.text-muted');
        
        if (pageTitle) {
            pageTitle.textContent = 'Редактирование пациента';
        }
        if (pageSubtitle) {
            pageSubtitle.textContent = 'Изменение данных пациента';
        }
    }

    async loadPatientData(patientId) {
        // Simulate API call to load patient data
        try {
            // Show loading state
            this.setFormLoading(true);

            const patientData = await this.simulateLoadPatient(patientId);
            this.populateForm(patientData);

            this.setFormLoading(false);
        } catch (error) {
            this.showToast('Ошибка загрузки данных пациента', 'error');
            this.setFormLoading(false);
        }
    }

    populateForm(patientData) {
        // Populate form fields with patient data
        const fields = {
            'lastName': patientData.lastName,
            'firstName': patientData.firstName,
            'middleName': patientData.middleName,
            'birthDate': this.formatDateForInput(patientData.birthDate),
            'phone': patientData.phone,
            'email': patientData.email,
            'address': patientData.address,
            'allergies': patientData.allergies,
            'chronicDiseases': patientData.chronicDiseases,
            'currentMedications': patientData.currentMedications,
            'familyHistory': patientData.familyHistory,
            'notes': patientData.notes
        };

        Object.keys(fields).forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element && fields[fieldId]) {
                element.value = fields[fieldId];
            }
        });

        // Set gender
        if (patientData.gender) {
            const genderRadio = document.querySelector(`input[name="gender"][value="${patientData.gender}"]`);
            if (genderRadio) {
                genderRadio.checked = true;
            }
        }
    }

    async handleSubmit() {
        if (!this.validateForm()) {
            this.showToast('Пожалуйста, исправьте ошибки в форме', 'warning');
            return;
        }

        const formData = this.getFormData();

        try {
            this.setFormLoading(true);

            if (this.isEditing) {
                await this.updatePatient(formData);
            } else {
                await this.createPatient(formData);
            }

            this.setFormLoading(false);
            this.clearDraft();
            
            this.showToast(
                this.isEditing ? 'Данные пациента обновлены' : 'Пациент успешно создан', 
                'success'
            );

            // Redirect to patients list
            setTimeout(() => {
                window.location.href = 'patient/patients.html';
            }, 1500);

        } catch (error) {
            this.setFormLoading(false);
            this.showToast('Ошибка сохранения данных', 'error');
        }
    }

    getFormData() {
        return {
            lastName: document.getElementById('lastName').value,
            firstName: document.getElementById('firstName').value,
            middleName: document.getElementById('middleName').value,
            birthDate: document.getElementById('birthDate').value,
            gender: document.querySelector('input[name="gender"]:checked')?.value,
            phone: document.getElementById('phone').value,
            email: document.getElementById('email').value,
            address: document.getElementById('address').value,
            allergies: document.getElementById('allergies').value,
            chronicDiseases: document.getElementById('chronicDiseases').value,
            currentMedications: document.getElementById('currentMedications').value,
            familyHistory: document.getElementById('familyHistory').value,
            notes: document.getElementById('notes').value,
            createdAt: new Date().toISOString()
        };
    }

    validateForm() {
        let isValid = true;
        const requiredFields = this.form.querySelectorAll('[required]');

        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        // Validate email if provided
        const emailInput = document.getElementById('email');
        if (emailInput && emailInput.value && !this.isValidEmail(emailInput.value)) {
            this.showFieldError(emailInput, 'Введите корректный email адрес');
            isValid = false;
        }

        return isValid;
    }

    validateField(field) {
        const value = field.value.trim();
        
        if (field.hasAttribute('required') && !value) {
            this.showFieldError(field, 'Это поле обязательно для заполнения');
            return false;
        }

        this.clearFieldError(field);
        return true;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('error');
        field.style.borderColor = 'var(--warning-color)';
        
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        
        field.parentNode.appendChild(errorElement);
    }

    clearFieldError(field) {
        field.classList.remove('error');
        field.style.borderColor = '';
        
        const existingError = field.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
    }

    saveDraft() {
        const formData = this.getFormData();
        const draftKey = this.isEditing ? `patient_draft_${this.patientId}` : 'patient_draft_new';
        
        localStorage.setItem(draftKey, JSON.stringify({
            ...formData,
            savedAt: new Date().toISOString()
        }));

        this.showToast('Черновик сохранен', 'success');
    }

    loadDraft() {
        if (this.isEditing) return; // Don't load draft in edit mode

        const draft = localStorage.getItem('patient_draft_new');
        if (draft) {
            try {
                const formData = JSON.parse(draft);
                this.populateForm(formData);
                this.showToast('Загружен сохраненный черновик', 'info');
            } catch (error) {
                console.error('Error loading draft:', error);
            }
        }
    }

    clearDraft() {
        const draftKey = this.isEditing ? `patient_draft_${this.patientId}` : 'patient_draft_new';
        localStorage.removeItem(draftKey);
    }

    // Utility methods
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    formatPhoneNumber(input) {
        let value = input.value.replace(/\D/g, '');
        
        if (value.startsWith('7') || value.startsWith('8')) {
            value = value.substring(1);
        }
        
        if (value.length > 0) {
            value = '+7 (' + value;
        }
        if (value.length > 7) {
            value = value.substring(0, 7) + ') ' + value.substring(7);
        }
        if (value.length > 12) {
            value = value.substring(0, 12) + '-' + value.substring(12);
        }
        if (value.length > 15) {
            value = value.substring(0, 15) + '-' + value.substring(15);
        }
        
        input.value = value;
    }

    formatDateForInput(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toISOString().split('T')[0];
    }

    setFormLoading(loading) {
        if (loading) {
            this.form.classList.add('form-loading');
        } else {
            this.form.classList.remove('form-loading');
        }
    }

    showToast(message, type = 'info') {
        // Simple toast implementation
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

    // Simulation methods (would be replaced with real API calls)
    simulateLoadPatient(patientId) {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    lastName: 'Петров',
                    firstName: 'Иван',
                    middleName: 'Сергеевич',
                    birthDate: '1985-03-15',
                    gender: 'male',
                    phone: '+7 (912) 345-67-89',
                    email: 'ivan.petrov@email.com',
                    address: 'г. Москва, ул. Примерная, д. 123',
                    allergies: 'Пенициллин',
                    chronicDiseases: 'Гипертония',
                    currentMedications: 'Лозартан 50мг ежедневно',
                    familyHistory: 'Сахарный диабет у матери',
                    notes: 'Пациент регулярно наблюдается'
                });
            }, 1000);
        });
    }

    createPatient(formData) {
        return new Promise((resolve) => {
            setTimeout(() => {
                console.log('Creating patient:', formData);
                resolve({ success: true, patientId: '#' + Math.random().toString(36).substr(2, 9).toUpperCase() });
            }, 1500);
        });
    }

    updatePatient(formData) {
        return new Promise((resolve) => {
            setTimeout(() => {
                console.log('Updating patient:', formData);
                resolve({ success: true });
            }, 1500);
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PatientForm();
});

