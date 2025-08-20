/**
 * UI utility functions for Matrica Networks
 * Handles modal management, form validation, and interactive components
 */

// Modal Management
class ModalManager {
    constructor() {
        this.activeModals = [];
        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeTopModal();
            }
        });
    }

    open(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        modal.classList.add('modal--active');
        this.activeModals.push(modalId);
        document.body.style.overflow = 'hidden';

        // Focus management
        const firstFocusable = modal.querySelector('input, button, textarea, select');
        if (firstFocusable) firstFocusable.focus();
    }

    close(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        modal.classList.remove('modal--active');
        this.activeModals = this.activeModals.filter(id => id !== modalId);
        
        if (this.activeModals.length === 0) {
            document.body.style.overflow = '';
        }
    }

    closeTopModal() {
        if (this.activeModals.length > 0) {
            const topModal = this.activeModals[this.activeModals.length - 1];
            this.close(topModal);
        }
    }

    closeAll() {
        this.activeModals.forEach(modalId => this.close(modalId));
        this.activeModals = [];
    }
}

// Form Validator
class FormValidator {
    constructor() {
        this.rules = {
            required: (value) => value.trim() !== '',
            email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            phone: (value) => /^[+]?[0-9\s\-\(\)]{10,15}$/.test(value),
            minLength: (value, length) => value.length >= length,
            maxLength: (value, length) => value.length <= length,
            password: (value) => value.length >= 8 && /(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)
        };
    }

    validate(field) {
        const value = field.value.trim();
        const rules = this.getFieldRules(field);
        
        for (const rule of rules) {
            const result = this.applyRule(value, rule);
            if (!result.valid) {
                this.showFieldError(field, result.message);
                return false;
            }
        }

        this.clearFieldError(field);
        return true;
    }

    getFieldRules(field) {
        const rules = [];
        
        if (field.hasAttribute('required')) {
            rules.push({ type: 'required', message: 'This field is required' });
        }

        if (field.type === 'email') {
            rules.push({ type: 'email', message: 'Please enter a valid email address' });
        }

        if (field.type === 'tel') {
            rules.push({ type: 'phone', message: 'Please enter a valid phone number' });
        }

        const minLength = field.getAttribute('minlength');
        if (minLength) {
            rules.push({ 
                type: 'minLength', 
                param: parseInt(minLength), 
                message: `Must be at least ${minLength} characters` 
            });
        }

        const maxLength = field.getAttribute('maxlength');
        if (maxLength) {
            rules.push({ 
                type: 'maxLength', 
                param: parseInt(maxLength), 
                message: `Must be no more than ${maxLength} characters` 
            });
        }

        return rules;
    }

    applyRule(value, rule) {
        const ruleFunction = this.rules[rule.type];
        if (!ruleFunction) return { valid: true };

        const valid = rule.param ? 
            ruleFunction(value, rule.param) : 
            ruleFunction(value);

        return {
            valid,
            message: valid ? '' : rule.message
        };
    }

    showFieldError(field, message) {
        field.classList.add('form__input--error');
        field.classList.remove('form__input--success');

        const errorElement = document.getElementById(`${field.name}-error`);
        if (errorElement) {
            errorElement.textContent = message;
        }
    }

    clearFieldError(field) {
        field.classList.remove('form__input--error');
        field.classList.add('form__input--success');

        const errorElement = document.getElementById(`${field.name}-error`);
        if (errorElement) {
            errorElement.textContent = '';
        }
    }

    validateForm(form) {
        const fields = form.querySelectorAll('input, textarea, select');
        let isValid = true;

        fields.forEach(field => {
            if (!this.validate(field)) {
                isValid = false;
            }
        });

        return isValid;
    }
}

// Loading Manager
class LoadingManager {
    show(element, text = 'Loading...') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }

        if (element) {
            element.classList.add('loading');
            element.setAttribute('data-original-text', element.textContent);
            element.textContent = text;
            element.disabled = true;
        }
    }

    hide(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }

        if (element) {
            element.classList.remove('loading');
            const originalText = element.getAttribute('data-original-text');
            if (originalText) {
                element.textContent = originalText;
                element.removeAttribute('data-original-text');
            }
            element.disabled = false;
        }
    }
}

// Notification System
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.notifications = [];
    }

    createContainer() {
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const notification = this.createNotification(message, type);
        this.container.appendChild(notification);
        this.notifications.push(notification);

        // Animate in
        setTimeout(() => notification.classList.add('notification--show'), 100);

        // Auto remove
        if (duration > 0) {
            setTimeout(() => this.remove(notification), duration);
        }

        return notification;
    }

    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification--${type}`;
        notification.innerHTML = `
            <div class="notification__content">
                <span class="notification__message">${message}</span>
                <button class="notification__close">&times;</button>
            </div>
        `;

        const closeBtn = notification.querySelector('.notification__close');
        closeBtn.addEventListener('click', () => this.remove(notification));

        return notification;
    }

    remove(notification) {
        if (!notification.parentNode) return;

        notification.classList.remove('notification--show');
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            this.notifications = this.notifications.filter(n => n !== notification);
        }, 300);
    }

    clear() {
        this.notifications.forEach(notification => this.remove(notification));
    }
}

// Data Table Manager
class DataTableManager {
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        this.options = {
            sortable: true,
            paginated: true,
            itemsPerPage: 10,
            searchable: true,
            ...options
        };
        
        this.data = [];
        this.filteredData = [];
        this.currentPage = 1;
        this.sortField = null;
        this.sortDirection = 'asc';
        this.searchQuery = '';

        this.init();
    }

    init() {
        if (this.options.sortable) {
            this.initSorting();
        }
        
        if (this.options.searchable) {
            this.initSearch();
        }
        
        if (this.options.paginated) {
            this.initPagination();
        }
    }

    setData(data) {
        this.data = data;
        this.filteredData = [...data];
        this.render();
    }

    render() {
        this.applyFilters();
        this.applySorting();
        this.renderTable();
        this.renderPagination();
    }

    applyFilters() {
        this.filteredData = this.data.filter(row => {
            if (!this.searchQuery) return true;
            
            return Object.values(row).some(value => 
                String(value).toLowerCase().includes(this.searchQuery.toLowerCase())
            );
        });
    }

    applySorting() {
        if (!this.sortField) return;

        this.filteredData.sort((a, b) => {
            const aVal = a[this.sortField];
            const bVal = b[this.sortField];
            
            if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }

    renderTable() {
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;

        const startIndex = (this.currentPage - 1) * this.options.itemsPerPage;
        const endIndex = startIndex + this.options.itemsPerPage;
        const pageData = this.filteredData.slice(startIndex, endIndex);

        tbody.innerHTML = pageData.map(row => this.renderRow(row)).join('');
    }

    renderRow(row) {
        // Override this method in subclasses
        return `<tr>${Object.values(row).map(val => `<td>${val}</td>`).join('')}</tr>`;
    }

    initSorting() {
        const headers = this.table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                const field = header.dataset.sort;
                this.sort(field);
            });
        });
    }

    sort(field) {
        if (this.sortField === field) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortField = field;
            this.sortDirection = 'asc';
        }

        this.render();
        this.updateSortIndicators();
    }

    updateSortIndicators() {
        const headers = this.table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.classList.remove('sort-asc', 'sort-desc');
            if (header.dataset.sort === this.sortField) {
                header.classList.add(`sort-${this.sortDirection}`);
            }
        });
    }

    search(query) {
        this.searchQuery = query;
        this.currentPage = 1;
        this.render();
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredData.length / this.options.itemsPerPage);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.renderTable();
            this.renderPagination();
        }
    }

    renderPagination() {
        if (!this.options.paginated) return;

        const totalPages = Math.ceil(this.filteredData.length / this.options.itemsPerPage);
        const paginationContainer = document.querySelector(`#${this.table.id}-pagination`);
        
        if (!paginationContainer || totalPages <= 1) return;

        let paginationHTML = '<div class="pagination">';
        
        // Previous button
        paginationHTML += `
            <button class="pagination__btn ${this.currentPage === 1 ? 'disabled' : ''}"
                    onclick="tableManager.goToPage(${this.currentPage - 1})"
                    ${this.currentPage === 1 ? 'disabled' : ''}>
                Previous
            </button>
        `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 1 && i <= this.currentPage + 1)) {
                paginationHTML += `
                    <button class="pagination__btn ${i === this.currentPage ? 'active' : ''}"
                            onclick="tableManager.goToPage(${i})">
                        ${i}
                    </button>
                `;
            } else if (i === this.currentPage - 2 || i === this.currentPage + 2) {
                paginationHTML += '<span class="pagination__ellipsis">...</span>';
            }
        }

        // Next button
        paginationHTML += `
            <button class="pagination__btn ${this.currentPage === totalPages ? 'disabled' : ''}"
                    onclick="tableManager.goToPage(${this.currentPage + 1})"
                    ${this.currentPage === totalPages ? 'disabled' : ''}>
                Next
            </button>
        `;

        paginationHTML += '</div>';
        paginationContainer.innerHTML = paginationHTML;
    }
}

// Initialize global instances
window.modals = new ModalManager();
window.validator = new FormValidator();
window.loading = new LoadingManager();
window.notifications = new NotificationManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ModalManager,
        FormValidator,
        LoadingManager,
        NotificationManager,
        DataTableManager
    };
}