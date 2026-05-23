document.addEventListener('DOMContentLoaded', () => {

    const publishedDateInput = document.getElementById('published-date');
    if (publishedDateInput) {
        publishedDateInput.valueAsDate = new Date();
    }

    // dynamic tag input 
    const input = document.getElementById('tag-input');
    const tagsContainer = document.getElementById('tags-container');
    const errorMessage = document.getElementById('error-message');
    const form = document.getElementById('thesis-form');
    const hiddenKeywords = document.getElementById('hidden-keywords');
    let tags = [];

    if (input && tagsContainer) {
        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && input.value.trim() !== '') {
                event.preventDefault(); // Prevent form submission
                
                const newTag = input.value.trim();
                
                if (tags.length >= 5) {
                    errorMessage.classList.remove('hidden');
                    return;
                } else {
                    errorMessage.classList.add('hidden');
                }

                if (!tags.includes(newTag)) {
                    tags.push(newTag);
                    renderTags();
                }
                input.value = '';
            }
        });

        // ensure the hidden input has the comma-separated tags before submission
        if (form && hiddenKeywords) {
            form.addEventListener('submit', () => {
                hiddenKeywords.value = tags.join(', ');
            });
        }

        const renderTags = () => {
            tagsContainer.innerHTML = '';
            tags.forEach((tag, index) => {
                const tagElement = document.createElement('div');
                tagElement.className = 'flex items-center bg-sage-200 text-sage-900 px-3 py-1 rounded-md text-sm font-bold shadow-sm';
                
                // Note: We use data-index here instead of an inline onclick string
                tagElement.innerHTML = `
                    <span>${tag}</span>
                    <button type="button" class="remove-tag-btn ml-2 text-sage-600 hover:text-red-600 transition font-black" data-index="${index}">
                      &times;
                    </button>
                `;
                tagsContainer.appendChild(tagElement);
            });
        };

        const removeTag = (index) => {
            tags.splice(index, 1);
            renderTags();
            errorMessage.classList.add('hidden'); 
        };

        tagsContainer.addEventListener('click', (e) => {
            const btn = e.target.closest('.remove-tag-btn');
            if (btn) {
                const index = parseInt(btn.getAttribute('data-index'), 10);
                removeTag(index);
            }
        });
    }

    const formatSelect = document.getElementById('format-select');
    const fileUpload = document.getElementById('file-upload');
    const fileContainer = document.getElementById('file-upload-container');

    if (formatSelect && fileUpload && fileContainer) {
        formatSelect.addEventListener('change', function() {
            const selectedText = this.options[this.selectedIndex].text.toLowerCase();
            
            if (selectedText.includes('hard copy')) {
                fileUpload.removeAttribute('required');
                fileUpload.disabled = true;
                fileContainer.style.opacity = '0.5';
                fileUpload.value = ""; // clear any attached file
            } else {
                fileUpload.setAttribute('required', 'required');
                fileUpload.disabled = false;
                fileContainer.style.opacity = '1';
            }
        });
    }

    function setupDynamicFormGroup(buttonId, containerId, groupClass, removeBtnClass) {
        const addBtn = document.getElementById(buttonId);
        const container = document.getElementById(containerId);

        if (addBtn && container) {
            addBtn.addEventListener('click', () => {
                const firstGroup = container.querySelector('.' + groupClass);
                if (!firstGroup) return;

                const newGroup = firstGroup.cloneNode(true);

                // clear all input values in the cloned group
                const inputs = newGroup.querySelectorAll('input');
                inputs.forEach(input => input.value = '');

                // remove button for the new clone
                const removeBtn = newGroup.querySelector('.' + removeBtnClass);
                if (removeBtn) {
                    removeBtn.classList.remove('hidden');
                    removeBtn.addEventListener('click', function() {
                        newGroup.remove();
                    });
                }

                container.appendChild(newGroup);
            });
        }
    }

    setupDynamicFormGroup('add-author-btn', 'authors-container', 'author-group', 'remove-author-btn');
    setupDynamicFormGroup('add-advisor-btn', 'advisors-container', 'advisor-group', 'remove-advisor-btn');

});
