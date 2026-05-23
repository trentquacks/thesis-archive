document.addEventListener('DOMContentLoaded', () => {
    const timeDisplay = document.getElementById('time-display');
    
    if (timeDisplay) {
        // fetch the time_left value from the HTML data attribute
        let timeLeft = parseInt(timeDisplay.dataset.timeLeft, 10);

        if (isNaN(timeLeft)) {
            timeLeft = 0; 
        }

        const countdown = setInterval(() => {
            if (timeLeft <= 0) {
                clearInterval(countdown);
                window.location.reload(); 
            } else {
                let hours = Math.floor(timeLeft / 3600);
                let minutes = Math.floor((timeLeft % 3600) / 60);
                let seconds = timeLeft % 60;
                
                timeDisplay.innerText = 
                    `${hours}:${minutes < 10 ? '0' : ''}${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
                
                timeLeft--;
            }
        }, 1000);
    }
});
