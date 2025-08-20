/* Theme Management System
 * Handles dark/light theme switching with localStorage persistence
 * Matrica Networks - Cybersecurity Company Website
 */

class ThemeManager {
    constructor() {
        this.themes = ['dark', 'light'];
        this.defaultTheme = 'dark';
        this.storageKey = 'matrica-theme-preference';
        
        this.init();
    }

    init() {
        // Get theme from localStorage or use system preference
        const savedTheme = this.getSavedTheme();
        const systemTheme = this.getSystemTheme();
        const initialTheme = savedTheme || systemTheme || this.defaultTheme;
        
        // Apply theme
        this.setTheme(initialTheme);
        
        // Setup theme toggle listeners
        this.setupToggleListeners();
        
        // Listen for system theme changes
        this.setupSystemThemeListener();
    }

    getSavedTheme() {
        try {
            return localStorage.getItem(this.storageKey);
        } catch (e) {
            console.warn('LocalStorage not available for theme persistence');
            return null;
        }
    }

    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            return 'light';
        }
        return 'dark';
    }

    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || this.defaultTheme;
    }

    setTheme(theme) {
        // Validate theme
        if (!this.themes.includes(theme)) {
            console.warn(`Invalid theme: ${theme}. Using default theme: ${this.defaultTheme}`);
            theme = this.defaultTheme;
        }

        // Apply theme to document
        document.documentElement.setAttribute('data-theme', theme);
        
        // Save to localStorage
        this.saveTheme(theme);
        
        // Update UI elements
        this.updateThemeUI(theme);
        
        // Dispatch custom event for other components
        this.dispatchThemeChangeEvent(theme);
    }

    saveTheme(theme) {
        try {
            localStorage.setItem(this.storageKey, theme);
        } catch (e) {
            console.warn('Failed to save theme preference');
        }
    }

    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        
        // Add toggle animation
        this.animateThemeTransition();
    }

    updateThemeUI(theme) {
        // Update theme toggle button aria-label
        const toggleButtons = document.querySelectorAll('.theme-toggle');
        toggleButtons.forEach(button => {
            button.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`);
        });

        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);
    }

    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }

        // Set appropriate theme color
        const colors = {
            dark: '#0a0a0a',
            light: '#ffffff'
        };
        
        metaThemeColor.content = colors[theme] || colors[this.defaultTheme];
    }

    animateThemeTransition() {
        // Add transition class to body for smooth theme switching
        document.body.classList.add('theme-transitioning');
        
        // Remove after animation completes
        setTimeout(() => {
            document.body.classList.remove('theme-transitioning');
        }, 300);
    }

    setupToggleListeners() {
        // Setup click listeners for all theme toggle buttons
        const toggleButtons = document.querySelectorAll('.theme-toggle');
        
        toggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleTheme();
            });

            // Add keyboard support
            button.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        });
    }

    setupSystemThemeListener() {
        // Listen for system theme changes if user hasn't set preference
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
            
            mediaQuery.addEventListener('change', (e) => {
                // Only auto-switch if user hasn't manually set a preference
                const savedTheme = this.getSavedTheme();
                if (!savedTheme) {
                    const systemTheme = e.matches ? 'light' : 'dark';
                    this.setTheme(systemTheme);
                }
            });
        }
    }

    dispatchThemeChangeEvent(theme) {
        // Dispatch custom event for other components to react to theme changes
        const event = new CustomEvent('themeChanged', {
            detail: {
                theme: theme,
                previousTheme: theme === 'dark' ? 'light' : 'dark'
            }
        });
        
        document.dispatchEvent(event);
    }

    // Public API methods
    reset() {
        try {
            localStorage.removeItem(this.storageKey);
        } catch (e) {
            console.warn('Failed to reset theme preference');
        }
        
        const systemTheme = this.getSystemTheme();
        this.setTheme(systemTheme);
    }

    // Get theme info for debugging
    getThemeInfo() {
        return {
            currentTheme: this.getCurrentTheme(),
            savedTheme: this.getSavedTheme(),
            systemTheme: this.getSystemTheme(),
            availableThemes: this.themes
        };
    }
}

// Add smooth theme transition styles
const themeTransitionStyles = `
    .theme-transitioning,
    .theme-transitioning *,
    .theme-transitioning *:before,
    .theme-transitioning *:after {
        transition: background-color 0.3s ease,
                    border-color 0.3s ease,
                    color 0.3s ease,
                    box-shadow 0.3s ease !important;
    }
    
    .theme-transitioning .theme-toggle .theme-icon {
        transition: opacity 0.3s ease, transform 0.3s ease !important;
    }
`;

// Inject transition styles
if (typeof document !== 'undefined') {
    const styleSheet = document.createElement('style');
    styleSheet.textContent = themeTransitionStyles;
    document.head.appendChild(styleSheet);
}

// Initialize theme manager when DOM is ready
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.themeManager = new ThemeManager();
        });
    } else {
        window.themeManager = new ThemeManager();
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}