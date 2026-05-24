document.addEventListener('DOMContentLoaded', () => {
    // logic to handle adding/removing dynamic author groups in edit wiew
    function setupDynamicFormGroup(buttonId, containerId, groupClass, removeBtnClass) {
        const addBtn = document.getElementById(buttonId);
        const container = document.getElementById(containerId);

        if (addBtn && container) {
            addBtn.addEventListener('click', () => {
                const firstGroup = container.querySelector('.' + groupClass);
                if (!firstGroup) return;

                const newGroup = firstGroup.cloneNode(true);
                const inputs = newGroup.querySelectorAll('input');
                inputs.forEach(input => input.value = ''); // clear cloned inputs

                const removeBtn = newGroup.querySelector('.' + removeBtnClass);
                if (removeBtn) {
                    removeBtn.classList.remove('hidden');
                    removeBtn.addEventListener('click', function() { newGroup.remove(); });
                }

                container.appendChild(newGroup);
            });
            
            // attach delete listener to existing rows keeping at least 1
            const existingRemoveBtns = container.querySelectorAll('.' + removeBtnClass);
            existingRemoveBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    const group = this.closest('.' + groupClass);
                    if (container.querySelectorAll('.' + groupClass).length > 1) group.remove();
                });
            });
        }
    }

    setupDynamicFormGroup('add-author-btn', 'authors-container', 'author-group', 'remove-author-btn');
    setupDynamicFormGroup('add-advisor-btn', 'advisors-container', 'advisor-group', 'remove-advisor-btn');
});
