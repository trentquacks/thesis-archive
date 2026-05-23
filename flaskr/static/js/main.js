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
