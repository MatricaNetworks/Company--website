/**
 * Matrica Networks - Authentication Check Module
 * Handles authentication verification and redirects for protected pages
 */

class AuthChecker {
    constructor() {
        this.apiBase = '/api';
        this.loginUrl = '/portal/login.html';
        this.isChecking = false;
    }

    /**
     * Check if user is authenticated
     * @returns {Promise<Object|null>} User data if authenticated, null otherwise
     */
    async checkAuth() {
        if (this.isChecking) {
            return null;
        }

        this.isChecking = true;

        try {
            const response = await fetch(`${this.apiBase}/me`, {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (response.ok && data.success && data.authenticated) {
                this.isChecking = false;
                return data.user;
            } else {
                this.isChecking = false;
                return null;
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.isChecking = false;
            return null;
        }
    }

    /**
     * Redirect to login page with return URL
     * @param {string} returnUrl - URL to return to after login
     */
    redirectToLogin(returnUrl = null) {
        const currentUrl = returnUrl || window.location.pathname + window.location.search;
        const loginUrlWithReturn = `${this.loginUrl}?returnUrl=${encodeURIComponent(currentUrl)}`;
        
        // Show a brief message before redirecting
        if (document.body) {
            this.showRedirectMessage();
        }
        
        setTimeout(() => {
            window.location.href = loginUrlWithReturn;
        }, 1000);
    }

    /**
     * Show a message while redirecting to login
     */
    showRedirectMessage() {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            color: #00ffff;
            font-family: 'Courier New', monospace;
        `;

        // Create message container
        const messageContainer = document.createElement('div');
        messageContainer.style.cssText = `
            text-align: center;
            padding: 2rem;
            border: 1px solid #00ffff;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.8);
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        `;

        // Create message
        const message = document.createElement('div');
        message.innerHTML = `
            <div style="font-size: 1.2rem; margin-bottom: 1rem;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 0.5rem;">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                Authentication Required
            </div>
            <div style="color: #888; font-size: 0.9rem;">
                Redirecting to login page...
            </div>
            <div style="margin-top: 1rem;">
                <div style="width: 200px; height: 4px; background: #333; border-radius: 2px; overflow: hidden; margin: 0 auto;">
                    <div style="width: 0%; height: 100%; background: linear-gradient(90deg, #00ffff, #00ff80); border-radius: 2px; animation: progress 1s ease-out forwards;"></div>
                </div>
            </div>
        `;

        // Add progress animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes progress {
                to { width: 100%; }
            }
        `;
        document.head.appendChild(style);

        messageContainer.appendChild(message);
        overlay.appendChild(messageContainer);
        document.body.appendChild(overlay);
    }

    /**
     * Require authentication for the current page
     * @param {string} requiredRole - Required user role (optional)
     * @returns {Promise<Object|null>} User data if authorized
     */
    async requireAuth(requiredRole = null) {
        const user = await this.checkAuth();

        if (!user) {
            this.redirectToLogin();
            return null;
        }

        // Check role if specified
        if (requiredRole && user.role !== requiredRole) {
            this.showAccessDenied(requiredRole);
            return null;
        }

        return user;
    }

    /**
     * Show access denied message
     * @param {string} requiredRole - Required role that user doesn't have
     */
    showAccessDenied(requiredRole) {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            color: #ff6b6b;
            font-family: 'Courier New', monospace;
        `;

        const messageContainer = document.createElement('div');
        messageContainer.style.cssText = `
            text-align: center;
            padding: 2rem;
            border: 1px solid #ff6b6b;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.8);
            box-shadow: 0 0 20px rgba(255, 107, 107, 0.3);
        `;

        messageContainer.innerHTML = `
            <div style="font-size: 1.2rem; margin-bottom: 1rem;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 0.5rem;">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="15" y1="9" x2="9" y2="15"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
                Access Denied
            </div>
            <div style="color: #888; font-size: 0.9rem; margin-bottom: 1rem;">
                You need ${requiredRole} privileges to access this page.
            </div>
            <button onclick="window.history.back()" style="
                background: transparent;
                border: 1px solid #ff6b6b;
                color: #ff6b6b;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                cursor: pointer;
                font-family: inherit;
            ">Go Back</button>
        `;

        overlay.appendChild(messageContainer);
        document.body.appendChild(overlay);
    }

    /**
     * Get current user info (cached for performance)
     * @returns {Promise<Object|null>} User data
     */
    async getCurrentUser() {
        if (this._currentUser) {
            return this._currentUser;
        }

        this._currentUser = await this.checkAuth();
        return this._currentUser;
    }

    /**
     * Clear cached user data (call on logout)
     */
    clearUserCache() {
        this._currentUser = null;
    }

    /**
     * Setup automatic session timeout checking
     * @param {number} checkInterval - How often to check (in milliseconds)
     */
    setupSessionTimeout(checkInterval = 300000) { // 5 minutes default
        if (this.timeoutInterval) {
            clearInterval(this.timeoutInterval);
        }

        this.timeoutInterval = setInterval(async () => {
            const user = await this.checkAuth();
            if (!user) {
                // Session expired
                this.showSessionExpired();
            }
        }, checkInterval);
    }

    /**
     * Show session expired message
     */
    showSessionExpired() {
        // Clear any existing timeout checks
        if (this.timeoutInterval) {
            clearInterval(this.timeoutInterval);
        }

        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            color: #ffd700;
            font-family: 'Courier New', monospace;
        `;

        const messageContainer = document.createElement('div');
        messageContainer.style.cssText = `
            text-align: center;
            padding: 2rem;
            border: 1px solid #ffd700;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.8);
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
        `;

        messageContainer.innerHTML = `
            <div style="font-size: 1.2rem; margin-bottom: 1rem;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 0.5rem;">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12,6 12,12 16,14"/>
                </svg>
                Session Expired
            </div>
            <div style="color: #888; font-size: 0.9rem; margin-bottom: 1rem;">
                Your session has expired for security reasons.<br>
                Please log in again to continue.
            </div>
            <button onclick="window.location.href='${this.loginUrl}?session_expired=true'" style="
                background: linear-gradient(90deg, #ffd700, #ffed4e);
                border: none;
                color: #000;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                cursor: pointer;
                font-family: inherit;
                font-weight: bold;
            ">Login Again</button>
        `;

        overlay.appendChild(messageContainer);
        document.body.appendChild(overlay);
    }
}

// Create global instance
window.authChecker = new AuthChecker();

// Auto-check authentication on page load for protected pages
document.addEventListener('DOMContentLoaded', () => {
    // Only auto-check on portal pages (not on login page itself)
    if (window.location.pathname.includes('/portal/') && !window.location.pathname.includes('login.html')) {
        // Determine required role based on URL
        let requiredRole = null;
        if (window.location.pathname.includes('admin.html')) {
            requiredRole = 'admin';
        }
        
        // Require authentication
        window.authChecker.requireAuth(requiredRole).then(user => {
            if (user) {
                // Setup session timeout checking
                window.authChecker.setupSessionTimeout();
                
                // Dispatch auth success event
                document.dispatchEvent(new CustomEvent('authSuccess', { detail: user }));
            }
        });
    }
});

// Utility functions for common auth operations
window.AuthUtils = {
    /**
     * Logout user
     */
    async logout() {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            // Clear user cache regardless of response
            window.authChecker.clearUserCache();

            // Redirect to login
            window.location.href = '/portal/login.html?logged_out=true';
        } catch (error) {
            console.error('Logout error:', error);
            // Force redirect even on error
            window.location.href = '/portal/login.html?logged_out=true';
        }
    },

    /**
     * Check if user has specific role
     * @param {string} role - Role to check
     * @returns {Promise<boolean>}
     */
    async hasRole(role) {
        const user = await window.authChecker.getCurrentUser();
        return user && user.role === role;
    },

    /**
     * Check if user is admin
     * @returns {Promise<boolean>}
     */
    async isAdmin() {
        return await this.hasRole('admin');
    }
};