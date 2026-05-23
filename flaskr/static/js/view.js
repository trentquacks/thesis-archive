document.addEventListener('DOMContentLoaded', () => {
    const copyBtn = document.getElementById('copy-btn');
    const abstractTextElement = document.getElementById('abstract-text');
    
    if (copyBtn && abstractTextElement) {
        copyBtn.addEventListener('click', () => {
            const abstractText = abstractTextElement.innerText;
            const originalHTML = '<i class="fa-solid fa-copy"></i> Copy';

            navigator.clipboard.writeText(abstractText).then(() => {
                copyBtn.innerHTML = '<i class="fa-solid fa-check text-green-600"></i> Copied!';
                setTimeout(() => { copyBtn.innerHTML = originalHTML; }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                alert('Failed to copy abstract. Please try highlighting the text manually.');
            });
        });
    }

    const copyCitationBtn = document.getElementById('copy-citation-btn');
    const citationTextElement = document.getElementById('citation-text');

    if (copyCitationBtn && citationTextElement) {
        copyCitationBtn.addEventListener('click', () => {
            const citationText = citationTextElement.innerText;
            const originalHTML = '<i class="fa-solid fa-copy"></i> Copy';

            navigator.clipboard.writeText(citationText).then(() => {
                copyCitationBtn.innerHTML = '<i class="fa-solid fa-check text-green-600"></i> Copied!';
                copyCitationBtn.classList.replace('bg-white', 'bg-green-50'); 
                copyCitationBtn.classList.replace('border-sage-200', 'border-green-200');

                setTimeout(() => {
                    copyCitationBtn.innerHTML = originalHTML;
                    copyCitationBtn.classList.replace('bg-green-50', 'bg-white');
                    copyCitationBtn.classList.replace('border-green-200', 'border-sage-200');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                alert('Failed to copy citation. Please try highlighting the text manually.');
            });
        });
    }

    const modal = document.getElementById('borrowModal');
    const openBtn = document.getElementById('open-borrow-btn');
    const closeBtns = document.querySelectorAll('.close-borrow-btn');

    if (modal) {
        const openModal = () => {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden'; 
        };

        const closeModal = () => {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto'; 
        };

        if (openBtn) {
            openBtn.addEventListener('click', openModal);
        }

        closeBtns.forEach(btn => {
            btn.addEventListener('click', closeModal);
        });

        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });

        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('borrow') === 'true') {
            
            const isActiveBorrow = modal.dataset.activeBorrow === 'true';
            
            if (!isActiveBorrow) {
                openModal();
            }
            
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }
});
