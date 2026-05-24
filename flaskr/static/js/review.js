document.addEventListener('DOMContentLoaded', () => {
    const setupModal = (actionType) => {
        const modal = document.getElementById(`${actionType}Modal`);
        const form = document.getElementById(`${actionType}Form`);
        const titleEl = document.getElementById(`${actionType}-thesis-title`);

        if (!modal) return;

        // open modal and inject data
        document.querySelectorAll(`.open-${actionType}-btn`).forEach(btn => {
            btn.addEventListener('click', (e) => {
                const btnEl = e.currentTarget;
                titleEl.textContent = btnEl.dataset.title;
                form.action = btnEl.dataset.url;
                modal.classList.remove('hidden');
                document.body.style.overflow = 'hidden'; // Prevent background scrolling
            });
        });

        // close modal via buttons
        document.querySelectorAll(`.close-${actionType}-btn`).forEach(btn => {
            btn.addEventListener('click', () => {
                modal.classList.add('hidden');
                document.body.style.overflow = 'auto'; // Restore scrolling
            });
        });

        // close modal by clicking outside the white box
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.add('hidden');
                document.body.style.overflow = 'auto';
            }
        });
    };

    ['approve', 'reject', 'delete'].forEach(setupModal);
});
