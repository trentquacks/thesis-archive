document.addEventListener('DOMContentLoaded', () => {
    
	// daily visit chart
    const visitsCtx = document.getElementById('visitsChart');
    if (visitsCtx) {
        const labels = JSON.parse(visitsCtx.dataset.labels || '[]');
        const guestData = JSON.parse(visitsCtx.dataset.guests || '[]');
        const registeredData = JSON.parse(visitsCtx.dataset.registered || '[]');

        new Chart(visitsCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Registered Users',
                        data: registeredData,
                        borderColor: '#568A45', 
                        backgroundColor: 'rgba(86, 138, 69, 0.1)',
                        borderWidth: 3,
                        tension: 0.4, 
                        fill: true,
                        pointBackgroundColor: '#568A45',
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Guests',
                        data: guestData,
                        borderColor: '#9ca3af', 
                        backgroundColor: 'rgba(156, 163, 175, 0.1)',
                        borderWidth: 3,
                        borderDash: [5, 5], 
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#9ca3af',
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top', labels: { font: { family: "'Inter', sans-serif", weight: 'bold' }, usePointStyle: true, padding: 20 } },
                    tooltip: { mode: 'index', intersect: false, backgroundColor: 'rgba(255, 255, 255, 0.95)', titleColor: '#1f2937', bodyColor: '#4b5563', borderColor: '#e5e7eb', borderWidth: 1, padding: 12, usePointStyle: true }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#f1f5f9', drawBorder: false }, ticks: { font: { family: "'Inter', sans-serif", weight: '600' }, color: '#64748b' } },
                    x: { grid: { display: false, drawBorder: false }, ticks: { font: { family: "'Inter', sans-serif", weight: '600' }, color: '#64748b' } }
                },
                interaction: { mode: 'nearest', axis: 'x', intersect: false }
            }
        });
    }

	// doughnut chart
    const deptCtx = document.getElementById('deptChart');
    if (deptCtx) {
        const deptLabels = JSON.parse(deptCtx.dataset.labels || '[]');
        const deptCounts = JSON.parse(deptCtx.dataset.counts || '[]');

        const distinctColors = [
            '#568A45', // Primary Sage Green
            '#3b82f6', // Bright Blue
            '#f59e0b', // Amber / Yellow
            '#8b5cf6', // Violet
            '#14b8a6', // Teal
            '#f43f5e', // Rose / Red
            '#0ea5e9', // Sky Blue
            '#84cc16', // Lime Green
            '#f97316', // Orange
            '#6366f1', // Indigo
            '#d946ef', // Fuchsia
            '#10b981'  // Emerald
        ];

        new Chart(deptCtx, {
            type: 'doughnut', 
            data: {
                labels: deptLabels,
                datasets: [{
                    data: deptCounts,
                    // If there are more departments than colors, Chart.js automatically loops this array
                    backgroundColor: distinctColors,
                    borderWidth: 2,           // Adds spacing between the slices
                    borderColor: '#ffffff',   // White borders make distinct colors pop without bleeding together
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%', 
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: { family: "'Inter', sans-serif", weight: '600' },
                            color: '#4b5563',
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#1f2937',
                        bodyColor: '#4b5563',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        padding: 12,
                        usePointStyle: true,
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                if (label) label += ': ';
                                if (context.parsed !== null) label += context.parsed + ' items';
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }
});
