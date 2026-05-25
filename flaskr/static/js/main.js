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

const VALID_THEMES = ['sage-light', 'dark', 'cvsu'];

let savedTheme = localStorage.getItem('theme');

if (!VALID_THEMES.includes(savedTheme)) {
    savedTheme = null;
}

const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const initialTheme = savedTheme || (systemPrefersDark ? 'dark' : 'sage-light');

document.documentElement.setAttribute('data-theme', initialTheme);

document.addEventListener('DOMContentLoaded', () => {
    const themeSelector = document.getElementById('theme-selector');

    if (themeSelector) {
        themeSelector.value = initialTheme;

        themeSelector.addEventListener('change', (e) => {
            const selectedTheme = e.target.value;
            // Only apply and save if it's a valid theme
            if (VALID_THEMES.includes(selectedTheme)) {
                document.documentElement.setAttribute('data-theme', selectedTheme);
                localStorage.setItem('theme', selectedTheme);
            }
        });
    }
});
