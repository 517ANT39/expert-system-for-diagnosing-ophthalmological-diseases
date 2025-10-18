// Patients management functionality
class PatientsManager {
    constructor() {
        this.patients = [];
        this.filteredPatients = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadPatients();
        this.setupSearch();
    }

    bindEvents() {
        // Search functionality
        const searchInput = document.getElementById('patientSearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => {
                this.searchPatients();
            }, 300));
        }

        // Filter changes
        const statusFilter = document.getElementById('statusFilter');
        const sortBy = document.getElementById('sortBy');
        
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                this.applyFilters();
            });
        }

        if (sortBy) {
            sortBy.addEventListener('change', () => {
                this.sortPatients();
            });
        }

        // Pagination
        document.addEventListener('click', (e) => {
            if (e.target.closest('.pagination .btn')) {
                this.handlePagination(e);
            }
        });
    }

    setupSearch() {
        // Quick search from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const searchQuery = urlParams.get('search');
        if (searchQuery) {
            document.getElementById('patientSearch').value = searchQuery;
            this.searchPatients();
        }
    }

    loadPatients() {
        // Simulate loading patients from API
        this.patients = [
            {
                id: 1,
                patientId: '#001',
                name: 'Петров Иван Сергеевич',
                email: 'ivan.petrov@email.com',
                phone: '',
                birthDate: '15.03.1985',
                gender: 'Мужской',
                lastConsultation: '20.01.2024',
                totalConsultations: 3,
                status: 'active'
            },
            {
                id: 2,
                patientId: '#002',
                name: 'Сидорова Мария Петровна',
                email: '',
                phone: '+7 (912) 345-67-89',
                birthDate: '22.07.1978',
                gender: 'Женский',
                lastConsultation: '19.01.2024',
                totalConsultations: 5,
                status: 'active'
            },
            {
                id: 3,
                patientId: '#003',
                name: 'Козлов Алексей Владимирович',
                email: 'alex.kozlov@email.com',
                phone: '',
                birthDate: '30.11.1992',
                gender: 'Мужской',
                lastConsultation: '18.01.2024',
                totalConsultations: 2,
                status: 'active'
            },
            {
                id: 4,
                patientId: '#004',
                name: 'Николаева Екатерина Игоревна',
                email: '',
                phone: '+7 (912) 123-45-67',
                birthDate: '14.05.1988',
                gender: 'Женский',
                lastConsultation: '15.01.2024',
                totalConsultations: 1,
                status: 'active'
            }
        ];

        this.filteredPatients = [...this.patients];
        this.renderPatients();
    }

    searchPatients() {
        const searchTerm = document.getElementById('patientSearch').value.toLowerCase();
        
        this.filteredPatients = this.patients.filter(patient => 
            patient.name.toLowerCase().includes(searchTerm) ||
            patient.patientId.toLowerCase().includes(searchTerm) ||
            (patient.email && patient.email.toLowerCase().includes(searchTerm)) ||
            (patient.phone && patient.phone.includes(searchTerm))
        );

        this.currentPage = 1;
        this.renderPatients();
    }

    applyFilters() {
        const statusFilter = document.getElementById('statusFilter').value;
        
        let filtered = [...this.patients];

        // Apply status filter
        if (statusFilter) {
            filtered = filtered.filter(patient => patient.status === statusFilter);
        }

        this.filteredPatients = filtered;
        this.currentPage = 1;
        this.renderPatients();
    }

    sortPatients() {
        const sortBy = document.getElementById('sortBy').value;
        
        this.filteredPatients.sort((a, b) => {
            switch(sortBy) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'date':
                    return new Date(b.lastConsultation) - new Date(a.lastConsultation);
                case 'lastVisit':
                    return new Date(b.lastConsultation) - new Date(a.lastConsultation);
                default:
                    return 0;
            }
        });

        this.renderPatients();
    }

    renderPatients() {
        const tbody = document.querySelector('#patientsTable tbody');
        const patientCount = document.getElementById('patientCount');
        
        if (!tbody) return;

        // Update patient count
        if (patientCount) {
            patientCount.textContent = this.filteredPatients.length;
        }

        // Calculate pagination
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const patientsToShow = this.filteredPatients.slice(startIndex, endIndex);

        // Render patients
        tbody.innerHTML = patientsToShow.map(patient => `
            <tr>
                <td>${patient.patientId}</td>
                <td>
                    <div class="patient-name">
                        <strong>${patient.name}</strong>
                        <span class="patient-contact">
                            ${patient.email || patient.phone}
                        </span>
                    </div>
                </td>
                <td>${patient.birthDate}</td>
                <td>${patient.gender}</td>
                <td>${patient.lastConsultation}</td>
                <td>${patient.totalConsultations}</td>
                <td>
                    <div class="action-buttons">
                        <a href="patient-history.html?patientId=${patient.id}" class="btn btn-sm btn-secondary">
                            📋 История
                        </a>
                        <a href="consultation.html?patientId=${patient.id}" class="btn btn-sm btn-primary">
                            🆕 Консультация
                        </a>
                    </div>
                </td>
            </tr>
        `).join('');

        this.updatePagination();
    }

    updatePagination() {
        const totalPages = Math.ceil(this.filteredPatients.length / this.itemsPerPage);
        const paginationContainer = document.querySelector('.pagination');
        
        if (!paginationContainer) return;

        const pageInfo = paginationContainer.querySelector('.page-info');
        const prevBtn = paginationContainer.querySelector('.btn:first-child');
        const nextBtn = paginationContainer.querySelector('.btn:last-child');

        if (pageInfo) {
            pageInfo.textContent = `Страница ${this.currentPage} из ${totalPages}`;
        }

        // Update button states
        if (prevBtn) {
            prevBtn.disabled = this.currentPage === 1;
        }
        if (nextBtn) {
            nextBtn.disabled = this.currentPage === totalPages;
        }
    }

    handlePagination(event) {
        const button = event.target.closest('.btn');
        if (!button || button.disabled) return;

        const isPrev = button.textContent.includes('Назад');
        const isNext = button.textContent.includes('Вперед');

        if (isPrev && this.currentPage > 1) {
            this.currentPage--;
        } else if (isNext && this.currentPage < Math.ceil(this.filteredPatients.length / this.itemsPerPage)) {
            this.currentPage++;
        }

        this.renderPatients();
        this.scrollToTop();
    }

    scrollToTop() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
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

    // Export functionality
    exportPatients() {
        const data = this.filteredPatients.map(patient => ({
            'ID пациента': patient.patientId,
            'ФИО': patient.name,
            'Дата рождения': patient.birthDate,
            'Пол': patient.gender,
            'Последняя консультация': patient.lastConsultation,
            'Всего консультаций': patient.totalConsultations
        }));

        // In a real app, this would generate CSV or Excel
        console.log('Exporting patients:', data);
        this.showToast('Данные пациентов готовы к экспорту', 'success');
    }
}

// Global search function
function searchPatients() {
    const searchInput = document.getElementById('patientSearch');
    if (searchInput) {
        const patientsManager = new PatientsManager();
        patientsManager.searchPatients();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PatientsManager();
});