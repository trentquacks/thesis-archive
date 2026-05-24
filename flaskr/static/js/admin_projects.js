document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('borrowsModal');
    const listContainer = document.getElementById('borrows-list');
    const sortSelect = document.getElementById('borrows-sort');
    const prevBtn = document.getElementById('borrows-prev');
    const nextBtn = document.getElementById('borrows-next');
    const pageInfo = document.getElementById('borrows-page-info');
    const titleEl = document.getElementById('borrows-thesis-title');
    const paginationContainer = document.getElementById('borrows-pagination');

    let currentThesisId = null;
    let currentPage = 1;
    let currentSort = 'newest';

    // open Modal and set active project
    document.querySelectorAll('.open-borrows-modal').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const button = e.currentTarget;
            currentThesisId = button.dataset.thesisId;
            titleEl.textContent = button.dataset.thesisTitle;
            
            // reset to defaults
            currentPage = 1;
            currentSort = 'newest';
            sortSelect.value = 'newest';

            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';

            fetchBorrows();
        });
    });

	// close modal logic
    const closeModal = () => {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    };

    document.querySelectorAll('.close-borrows-btn').forEach(btn => btn.addEventListener('click', closeModal));
    modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });

	// calls admin.py api
    const fetchBorrows = async () => {
        listContainer.innerHTML = '<div class="flex justify-center items-center h-full text-sage-400 py-8"><i class="fa-solid fa-spinner fa-spin text-3xl"></i></div>';
        paginationContainer.classList.add('hidden');

        try {
            const res = await fetch(`/admin/api/thesis/${currentThesisId}/borrows?page=${currentPage}&sort=${currentSort}`);
            const data = await res.json();
            renderList(data);
        } catch (err) {
            listContainer.innerHTML = '<div class="text-center text-red-500 py-4 font-bold">Failed to load borrow history. Please try again.</div>';
        }
    };

	// renders json
    const renderList = (data) => {
        if (data.borrows.length === 0) {
            listContainer.innerHTML = '<div class="flex flex-col items-center justify-center h-full text-sage-500 py-8 font-bold"><i class="fa-regular fa-folder-open text-4xl mb-2 opacity-50"></i>No borrow history found.</div>';
            return;
        }

        listContainer.innerHTML = data.borrows.map(b => `
            <div class="bg-sage-50 rounded-xl p-3 border border-sage-200 flex items-center gap-4 transition hover:shadow-sm">
                <img src="${b.profile_pic}" alt="Profile" 
                     class="w-12 h-12 rounded-full object-cover border-2 border-white shadow-sm shrink-0" 
                     onerror="this.onerror=null; this.src='/static/profile_pics/default.png';">
                     
                <div class="flex flex-col flex-1 min-w-0">
                    <span class="font-extrabold text-sage-900 truncate text-base">${b.name}</span>
                    <span class="text-xs font-medium text-sage-500 mt-0.5"><i class="fa-regular fa-clock mr-1"></i>${b.date}</span>
                </div>
            </div>
        `).join('');

        // handle pagination state
        if (data.pages > 1) {
            paginationContainer.classList.remove('hidden');
            pageInfo.textContent = `PAGE ${data.current_page} OF ${data.pages}`;
            prevBtn.disabled = data.current_page <= 1;
            nextBtn.disabled = data.current_page >= data.pages;
        }
    };

    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; fetchBorrows(); }
    });

    nextBtn.addEventListener('click', () => {
        currentPage++; fetchBorrows();
    });
});
