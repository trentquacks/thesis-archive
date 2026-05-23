document.addEventListener('DOMContentLoaded', () => {
	// change profile pic
    const profilePicTrigger = document.getElementById('profile-pic-trigger');
    const fileUploadInput = document.getElementById('file-upload');
    const picForm = document.getElementById('pic-form');

    if (profilePicTrigger && fileUploadInput) {
        profilePicTrigger.addEventListener('click', () => {
            fileUploadInput.click();
        });
    }

    if (fileUploadInput && picForm) {
        fileUploadInput.addEventListener('change', () => {
            picForm.submit();
        });
    }
});
