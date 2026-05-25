document.addEventListener('DOMContentLoaded', () => {

    // AJAX bookmark toggle ---
    document.querySelectorAll('.ajax-bookmark').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault(); // stop the form from reloading the page

            const btn = form.querySelector('button');
            const icon = form.querySelector('i');

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                if (response.ok) {
                    const data = await response.json();
                    
                    if (data.bookmarked) {
                        icon.classList.replace('fa-regular', 'fa-solid');
                        btn.classList.remove('bg-theme-secondary', 'text-theme-text', 'hover:bg-theme-border');
                        btn.classList.add('bg-theme-primary', 'text-white', 'hover:bg-theme-primary-hover');
                        btn.title = "Remove Bookmark";
                    } else {
                        icon.classList.replace('fa-solid', 'fa-regular');
                        btn.classList.remove('bg-theme-primary', 'text-white', 'hover:bg-theme-primary-hover');
                        btn.classList.add('bg-theme-secondary', 'text-theme-text', 'hover:bg-theme-border');
                        btn.title = "Save Bookmark";
                    }

                    if (data.message) {
                         showToast(data.message);
                    }
                }
            } catch (error) {
                console.error("Network error during bookmark toggle:", error);
            }
        });
    });

    // dynamic toast notification
    function showToast(message) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'pointer-events-auto flex items-start justify-between p-4 rounded-xl font-bold border shadow-lg bg-theme-surface text-theme-text border-theme-border transition-all duration-300';
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="flex items-center gap-3">
                <i class="fa-solid fa-circle-check text-xl"></i>
                <span>${message}</span>
            </div>
            <button type="button" class="ml-4 text-lg opacity-60 hover:opacity-100 transition focus:outline-none" onclick="this.closest('[role=\\'alert\\']').remove();">
                <i class="fa-solid fa-xmark"></i>
            </button>
        `;
        
        container.appendChild(toast);

        // Fade out and remove
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    const dateBtn = document.getElementById('sort-date-btn');
    const alphaBtn = document.getElementById('sort-alpha-btn');
    const yearFilter = document.getElementById('year-filter'); 

    // function to update URL parameters and reload the page
    function updateURLParameterAndReload(key, value) {
        const urlParams = new URLSearchParams(window.location.search);
        if (value) urlParams.set(key, value);
        else urlParams.delete(key); 
        
        if (key !== 'page') urlParams.set('page', 1); // reset to page 1 on new filter/sort

        window.location.href = window.location.pathname + '?' + urlParams.toString(); 
    }

    // date sorting button
    if (dateBtn) {
        dateBtn.addEventListener('click', (e) => {
            e.preventDefault(); 
            const currentState = dateBtn.getAttribute('data-state');
            const nextState = currentState === 'newest' ? 'oldest' : 'newest';
            updateURLParameterAndReload('sort', nextState);
        });
    }

    // alphabetical sorting button
    if (alphaBtn) {
        alphaBtn.addEventListener('click', (e) => {
            e.preventDefault();
            // Pulling state directly from the data-state attribute you set in HTML
            const currentState = alphaBtn.getAttribute('data-state');
            const nextState = currentState === 'az' ? 'za' : 'az';
            updateURLParameterAndReload('sort', nextState);
        });
    }

    // year dropdown filter
    if (yearFilter) {
        yearFilter.addEventListener('change', (e) => {
            updateURLParameterAndReload('year', e.target.value);
        });
    }
});
