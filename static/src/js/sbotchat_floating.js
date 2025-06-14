/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * SBot Chat Global Floating Button
 * Hiển thị button floating với chữ SBOT để mở chat interface
 */
class SbotchatFloatingButton extends Component {
    static template = "sbotchat.FloatingButton";

    setup() {
        this.action = useService('action');
        
        onMounted(() => {
            this.initializeFloatingButton();
        });
    }

    /**
     * Initialize floating button
     */
    initializeFloatingButton() {
        console.log("🎯 SBot Floating Button đã được khởi tạo");
    }

    /**
     * Open chat interface
     */
    openChat() {
        try {
            console.log("🚀 Mở SBot Chat từ floating button...");
            
            // Hide floating button
            this.hideFloatingButton();
            
            // Open chat interface
            this.action.doAction({
                type: 'ir.actions.client',
                tag: 'sbotchat.interface',
                name: 'SBot Chat',
                target: 'fullscreen'
            });
            
        } catch (error) {
            console.error("❌ Không thể mở SBot Chat:", error);
            this.showNotification("Không thể mở giao diện chat", "danger");
        }
    }

    /**
     * Hide floating button
     */
    hideFloatingButton() {
        const floatingBtn = document.querySelector('.sbotchat-global-floating-btn');
        if (floatingBtn) {
            floatingBtn.style.display = 'none';
        }
    }

    /**
     * Show floating button
     */
    showFloatingButton() {
        const floatingBtn = document.querySelector('.sbotchat-global-floating-btn');
        if (floatingBtn) {
            floatingBtn.style.display = 'flex';
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Create custom notification
        const notification = document.createElement('div');
        notification.className = `custom-notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 0.75rem;
            color: #0f172a;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            z-index: 9999;
            transform: translateX(100%);
            transition: all 0.3s ease;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <i class="fa fa-${type === 'success' ? 'check' : type === 'danger' ? 'times' : 'info'}-circle"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Auto remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 4000);
    }
}

/**
 * Global Floating Button Manager
 * Quản lý việc hiển thị floating button trên toàn bộ Odoo
 */
class SbotchatGlobalManager {
    constructor() {
        this.floatingButton = null;
        this.isInitialized = false;
    }

    /**
     * Initialize global floating button
     */
    init() {
        if (this.isInitialized) return;
        
        try {
            console.log("🌐 Khởi tạo SBot Global Manager...");
            
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.createFloatingButton());
            } else {
                this.createFloatingButton();
            }
            
            this.isInitialized = true;
            console.log("✅ SBot Global Manager đã khởi tạo thành công");
            
        } catch (error) {
            console.error("❌ Lỗi khởi tạo SBot Global Manager:", error);
        }
    }

    /**
     * Create floating button element
     */
    createFloatingButton() {
        // Remove existing button if any
        this.removeFloatingButton();
        
        // Create floating button
        const floatingBtn = document.createElement('div');
        floatingBtn.className = 'sbotchat-global-floating-btn';
        floatingBtn.innerHTML = `
            <span class="sbot-text">SBOT</span>
            <div class="tooltip">Mở SBot Chat</div>
        `;
        
        // Add click event
        floatingBtn.addEventListener('click', () => this.openChat());
        
        // Add to body
        document.body.appendChild(floatingBtn);
        this.floatingButton = floatingBtn;
        
        console.log("🎯 Floating button đã được tạo");
    }

    /**
     * Remove floating button
     */
    removeFloatingButton() {
        const existingBtn = document.querySelector('.sbotchat-global-floating-btn');
        if (existingBtn && existingBtn.parentNode) {
            existingBtn.parentNode.removeChild(existingBtn);
        }
        this.floatingButton = null;
    }

    /**
     * Open chat interface
     */
    openChat() {
        try {
            console.log("🚀 Mở SBot Chat từ global manager...");
            
            // Hide floating button
            if (this.floatingButton) {
                this.floatingButton.style.display = 'none';
            }
            
            // Try to use Odoo's action service
            if (window.odoo && window.odoo.define) {
                // Use Odoo's action system
                const actionService = window.odoo.__DEBUG__.services['action'];
                if (actionService) {
                    actionService.doAction({
                        type: 'ir.actions.client',
                        tag: 'sbotchat.interface',
                        name: 'SBot Chat',
                        target: 'fullscreen'
                    });
                    return;
                }
            }
            
            // Fallback: direct navigation
            window.location.href = '/web#action=sbotchat.interface';
            
        } catch (error) {
            console.error("❌ Không thể mở SBot Chat:", error);
            // Fallback: try direct URL
            window.location.href = '/web#action=sbotchat.interface';
        }
    }

    /**
     * Show floating button
     */
    showFloatingButton() {
        if (this.floatingButton) {
            this.floatingButton.style.display = 'flex';
        } else {
            this.createFloatingButton();
        }
    }

    /**
     * Hide floating button
     */
    hideFloatingButton() {
        if (this.floatingButton) {
            this.floatingButton.style.display = 'none';
        }
    }
}

// Create global instance
const sbotchatGlobalManager = new SbotchatGlobalManager();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => sbotchatGlobalManager.init());
} else {
    sbotchatGlobalManager.init();
}

// Export for use in other modules
window.sbotchatGlobalManager = sbotchatGlobalManager;

// Register floating button component
registry.category("actions").add("sbotchat.floating", SbotchatFloatingButton);

export { SbotchatFloatingButton, sbotchatGlobalManager }; 