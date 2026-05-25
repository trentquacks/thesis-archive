document.addEventListener('DOMContentLoaded', () => {
    // toast notification removal
    const toastCloseBtns = document.querySelectorAll('.toast-close-btn');
    
    toastCloseBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const alertBox = this.closest('[role="alert"]');
            if (alertBox) {
                alertBox.remove();
            }
        });
    });
});

// theme toggler

const savedTheme = localStorage.getItem('theme');
const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const initialTheme = savedTheme || (systemPrefersDark ? 'dark' : 'sage-light');

document.documentElement.setAttribute('data-theme', initialTheme);

document.addEventListener('DOMContentLoaded', () => {
    const themeSelector = document.getElementById('theme-selector');

    if (themeSelector) {
        themeSelector.value = initialTheme;

        themeSelector.addEventListener('change', (e) => {
            const selectedTheme = e.target.value;
            document.documentElement.setAttribute('data-theme', selectedTheme);
            localStorage.setItem('theme', selectedTheme);
        });
    }
});
