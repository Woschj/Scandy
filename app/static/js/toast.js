class Toast {
    constructor() {
        this.createToastContainer();
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
        document.body.appendChild(container);
    }

    show(message, type = 'info') {
        const toast = document.createElement('div');
        const colors = {
            success: 'alert-success',
            error: 'alert-error',
            info: 'alert-info',
            warning: 'alert-warning'
        };

        toast.className = `alert ${colors[type]} shadow-lg transition-all duration-300 ease-in-out translate-x-full`;
        toast.innerHTML = `
            <div class="flex items-center gap-2">
                <i class="fas fa-${this.getIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        const container = document.getElementById('toast-container');
        container.appendChild(toast);

        // Animation einblenden
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);

        // Nach 3 Sekunden ausblenden
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                container.removeChild(toast);
            }, 300);
        }, 3000);
    }

    getIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            info: 'info-circle',
            warning: 'exclamation-triangle'
        };
        return icons[type] || 'info-circle';
    }
}

// Globale Instanz
window.toast = new Toast(); 