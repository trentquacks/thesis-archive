document.addEventListener('DOMContentLoaded', () => {
    
    // borrowed thesis countdown timers 
    const timerElements = document.querySelectorAll('.borrow-timer');

    timerElements.forEach(timerElement => {
        let timeLeft = parseInt(timerElement.getAttribute('data-time'), 10);

        if (isNaN(timeLeft)) return;

        const countdown = setInterval(() => {
            if (timeLeft <= 0) {
                clearInterval(countdown);
                timerElement.innerText = "Expired";
                
                // Safely update the parent container's color if it exists
                const timeContainer = timerElement.closest('.time-container');
                if (timeContainer) {
                    timeContainer.classList.replace('text-red-600', 'text-gray-500');
                }
            } else {
                let hours = Math.floor(timeLeft / 3600);
                let minutes = Math.floor((timeLeft % 3600) / 60);
                let seconds = timeLeft % 60;

                timerElement.innerText = `${hours}h ${minutes}m ${seconds}s`;
                timeLeft--;
            }
        }, 1000);
    });

});
