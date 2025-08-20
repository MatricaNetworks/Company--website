/**
 * Main JavaScript file for Matrica Networks website
 * Handles global functionality, navigation, and UI interactions
 */

// Global application state
window.MatricaApp = {
    isAuthenticated: false,
    currentUser: null,
    csrfToken: null,
    theme: 'dark',
    themeManager: null
};

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize core functionality
    initializeNavigation();
    initializeTheme();
    initializeAnimations();
    initializeMatrixRain();
    initializeScrollEffects();
    initializeForms();
    
    // Check if user is authenticated
    checkAuthenticationStatus();
});

/**
 * Navigation Management
 */
function initializeNavigation() {
    // Mobile navigation toggle
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    const navClose = document.getElementById('nav-close');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.add('show-menu');
        });
    }

    if (navClose && navMenu) {
        navClose.addEventListener('click', () => {
            navMenu.classList.remove('show-menu');
        });
    }

    // Close menu when clicking on a link
    const navLinks = document.querySelectorAll('.nav__link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (navMenu) {
                navMenu.classList.remove('show-menu');
            }
        });
    });

    // Header scroll effect
    const header = document.getElementById('header');
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY >= 100) {
                header.classList.add('scroll-header');
            } else {
                header.classList.remove('scroll-header');
            }
        });
    }

    // Active navigation highlighting
    highlightActiveNavigation();
}

/**
 * Theme Management (Legacy compatibility with new ThemeManager)
 */
function initializeTheme() {
    // Theme management is now handled by the ThemeManager class in theme.js
    // This function maintains compatibility with existing code
    
    // Listen for theme changes to update global app state
    document.addEventListener('themeChanged', (event) => {
        MatricaApp.theme = event.detail.theme;
    });
    
    // Set initial theme in global state
    if (window.themeManager) {
        MatricaApp.theme = window.themeManager.getCurrentTheme();
    }
}

// Legacy functions for backward compatibility
function applyTheme(theme) {
    if (window.themeManager) {
        window.themeManager.setTheme(theme);
    } else {
        // Fallback if ThemeManager not available
        document.documentElement.setAttribute('data-theme', theme);
        MatricaApp.theme = theme;
        try {
            localStorage.setItem('matrica-theme-preference', theme);
        } catch (e) {
            console.warn('Failed to save theme preference');
        }
    }
}

function toggleTheme() {
    if (window.themeManager) {
        window.themeManager.toggleTheme();
    } else {
        // Fallback toggle
        const currentTheme = MatricaApp.theme;
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    }
}

/**
 * Animation Management
 */
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
            }
        });
    }, observerOptions);

    // Observe all elements with animation attributes
    const animatedElements = document.querySelectorAll('[data-animation]');
    animatedElements.forEach(el => observer.observe(el));

    // Neon glow effects
    initializeNeonEffects();
}

function initializeNeonEffects() {
    const neonElements = document.querySelectorAll('.neon-text, [data-animation="glow"]');
    
    neonElements.forEach(element => {
        element.addEventListener('mouseenter', () => {
            element.classList.add('neon-glow-active');
        });

        element.addEventListener('mouseleave', () => {
            element.classList.remove('neon-glow-active');
        });
    });
}

/**
 * Matrix Rain Background Effect
 */
class MatrixRain {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
        this.initializeDrops();
        this.animate();

        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.columns = Math.floor(this.canvas.width / 20);
        this.initializeDrops();
    }

    initializeDrops() {
        this.drops = [];
        for (let i = 0; i < this.columns; i++) {
            this.drops[i] = 1;
        }
    }

    animate() {
        // Semi-transparent black background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.04)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Matrix characters
        this.ctx.fillStyle = '#00ff9f';
        this.ctx.font = '15px monospace';

        const chars = '10アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';

        for (let i = 0; i < this.drops.length; i++) {
            const text = chars[Math.floor(Math.random() * chars.length)];
            this.ctx.fillText(text, i * 20, this.drops[i] * 20);

            if (this.drops[i] * 20 > this.canvas.height && Math.random() > 0.975) {
                this.drops[i] = 0;
            }
            this.drops[i]++;
        }

        requestAnimationFrame(() => this.animate());
    }
}

function initializeMatrixRain() {
    // Initialize matrix rain on pages that have the canvas
    if (document.getElementById('matrix-rain')) {
        new MatrixRain('matrix-rain');
    }
}

/**
 * Scroll Effects
 */
function initializeScrollEffects() {
    // Parallax effects
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const parallax = document.querySelectorAll('.parallax');
        
        parallax.forEach(element => {
            const speed = element.dataset.speed || 0.5;
            const yPos = -(scrolled * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });
    });

    // Progress bar for long content
    const progressBar = document.querySelector('.reading-progress');
    if (progressBar) {
        window.addEventListener('scroll', updateReadingProgress);
    }
}

function updateReadingProgress() {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = (scrollTop / docHeight) * 100;
    
    const progressBar = document.querySelector('.reading-progress');
    if (progressBar) {
        progressBar.style.width = scrollPercent + '%';
    }
}

/**
 * Form Management
 */
function initializeForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Add loading states
        form.addEventListener('submit', handleFormSubmit);
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', clearFieldError);
        });
    });
}

function handleFormSubmit(event) {
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (submitBtn) {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
    }
}

function validateField(event) {
    const field = event.target;
    const fieldName = field.name;
    const value = field.value.trim();
    const errorElement = document.querySelector(`#${fieldName}-error`);
    
    let isValid = true;
    let errorMessage = '';

    // Basic validation rules
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    } else if (field.type === 'email' && value && !isValidEmail(value)) {
        isValid = false;
        errorMessage = 'Please enter a valid email address';
    }

    updateFieldValidation(field, errorElement, isValid, errorMessage);
}

function clearFieldError(event) {
    const field = event.target;
    const errorElement = document.querySelector(`#${field.name}-error`);
    
    if (errorElement && errorElement.textContent) {
        errorElement.textContent = '';
        field.classList.remove('error');
    }
}

function updateFieldValidation(field, errorElement, isValid, errorMessage) {
    if (isValid) {
        field.classList.remove('error');
        field.classList.add('valid');
        if (errorElement) errorElement.textContent = '';
    } else {
        field.classList.add('error');
        field.classList.remove('valid');
        if (errorElement) errorElement.textContent = errorMessage;
    }
}

/**
 * Authentication Management
 */
async function checkAuthenticationStatus() {
    try {
        const response = await fetch('/api/me');
        if (response.ok) {
            const data = await response.json();
            MatricaApp.isAuthenticated = data.authenticated;
            MatricaApp.currentUser = data.user;
        }
    } catch (error) {
        console.error('Failed to check authentication status:', error);
    }
}

/**
 * Navigation Highlighting
 */
function highlightActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav__link');
    
    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath || 
            (currentPath.includes('portal') && link.href.includes('portal'))) {
            link.classList.add('nav__link--active');
        }
    });
}

/**
 * Utility Functions
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function debounce(func, wait) {
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

function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification--${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add('show'), 100);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Make key functions globally available
window.MatrixRain = MatrixRain;
window.showNotification = showNotification;
window.formatDate = formatDate;