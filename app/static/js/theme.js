// Theme handling
document.addEventListener('DOMContentLoaded', function() {
    const themeController = document.querySelector('.theme-controller');
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'winter';
    document.documentElement.setAttribute('data-theme', savedTheme);
    themeController.checked = savedTheme === 'dark';
    
    // Theme toggle handler
    themeController.addEventListener('change', function() {
        const newTheme = this.checked ? 'dark' : 'winter';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}); 