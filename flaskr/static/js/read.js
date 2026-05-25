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

document.addEventListener('DOMContentLoaded', () => {
    
    // --- PDF.js Logic ---
    const canvas = document.querySelector('#pdf-render');
    if (!canvas) return; // Exit if not on the read page

    // Grab the URL injected by Jinja in the HTML
    const url = canvas.getAttribute('data-pdf-url');
    if (!url) return;

    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

    let pdfDoc = null,
        pageNum = 1,
        pageIsRendering = false,
        pageNumIsPending = null;

    const scale = 1.5, // Adjust this to make the PDF render larger or smaller
          ctx = canvas.getContext('2d');

    const renderPage = num => {
        pageIsRendering = true;

        pdfDoc.getPage(num).then(page => {
            const viewport = page.getViewport({ scale });
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            const renderCtx = {
                canvasContext: ctx,
                viewport: viewport
            };

            page.render(renderCtx).promise.then(() => {
                pageIsRendering = false;

                if (pageNumIsPending !== null) {
                    renderPage(pageNumIsPending);
                    pageNumIsPending = null;
                }
            });

            document.querySelector('#page-num').textContent = num;
        });
    };

    const queueRenderPage = num => {
        if (pageIsRendering) {
            pageNumIsPending = num;
        } else {
            renderPage(num);
        }
    };

    const showPrevPage = () => {
        if (pageNum <= 1) return;
        pageNum--;
        queueRenderPage(pageNum);
    };

    const showNextPage = () => {
        if (pageNum >= pdfDoc.numPages) return;
        pageNum++;
        queueRenderPage(pageNum);
    };

    pdfjsLib.getDocument(url).promise.then(pdfDoc_ => {
        pdfDoc = pdfDoc_;
        
        document.querySelector('#page-count').textContent = pdfDoc.numPages;

        renderPage(pageNum);
    }).catch(err => {
        console.error("Error loading PDF: ", err);
        ctx.font = "16px serif";
        ctx.fillText("Failed to load PDF.", 50, 50);
    });

    document.querySelector('#prev-page').addEventListener('click', showPrevPage);
    document.querySelector('#next-page').addEventListener('click', showNextPage);

});
