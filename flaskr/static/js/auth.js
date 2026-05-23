document.addEventListener("DOMContentLoaded", function() {
    
    // student umber formatting 
    const studentNoInput = document.getElementById('student_no');
    if (studentNoInput) {
        studentNoInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9-]/g, '');
        });
    }

	// password visibility toggle
    const toggleButtons = document.querySelectorAll('.toggle-password');
    if (toggleButtons.length > 0) {
        toggleButtons.forEach(button => {
            button.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const input = document.getElementById(targetId);
                const icon = this.querySelector('i');
                
                if (input && input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                } else if (input) {
                    input.type = 'password';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                }
            });
        });
    }
});
