let graficoSospechoso = null;

$(document).on('click', '#btn-cargar-sospechoso', function () {
    const token = localStorage.getItem('token');

    $.ajax({
        url: 'http://localhost:8000/api/v1/cfdi/prediccion-sospechoso',
        method: 'GET',
        headers: {
            Authorization: `Bearer ${token}`
        },
        success: function (data) {
            const totalSospechosos = data.filter(cfdi => cfdi.sospechoso).length;
            const totalNoSospechosos = data.length - totalSospechosos;

            const ctx = document.getElementById('graficoSospechosos').getContext('2d');

            if (graficoSospechoso !== null) {
                graficoSospechoso.destroy();
            }
            
            graficoSospechoso = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['Sospechosos', 'No Sospechosos'],
                    datasets: [{
                        label: 'CFDIs',
                        data: [totalSospechosos, totalNoSospechosos],
                        backgroundColor: ['#dc3545', '#28a745'],
                        borderColor: ['#ffffff', '#ffffff'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                font: {
                                    size: 14
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        },
        error: function () {
            alert("Error al obtener CFDIs sospechosos.");
        }
    });
});
