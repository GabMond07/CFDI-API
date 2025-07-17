let graficoPrediccion = null;

$(document).on('click', '#btn-cargar-grafica', function () {
    const token = localStorage.getItem('token');

    $.ajax({
        url: 'http://localhost:8000/api/v1/ml/clasificar',
        method: 'GET',
        headers: {
            Authorization: `Bearer ${token}`
        },
        success: function (data) {
            const etiquetas = [];
            const aciertos = [];
            const errores = [];

            data.forEach(item => {
                const tipo = item.prediccion;
                const esperado = item.esperado;
                const index = etiquetas.indexOf(tipo);

                if (index === -1) {
                    etiquetas.push(tipo);
                    aciertos.push(tipo === esperado ? 1 : 0);
                    errores.push(tipo !== esperado ? 1 : 0);
                } else {
                    if (tipo === esperado) {
                        aciertos[index]++;
                    } else {
                        errores[index]++;
                    }
                }
            });

            const ctx = document.getElementById('graficaPredicciones').getContext('2d');

            if (graficoPrediccion !== null) {
                graficoPrediccion.destroy();
            }

            graficoPrediccion = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: etiquetas,
                    datasets: [
                        {
                            label: 'Aciertos',
                            backgroundColor: 'rgba(75, 192, 192, 0.7)',
                            data: aciertos
                        },
                        {
                            label: 'Errores',
                            backgroundColor: 'rgba(255, 99, 132, 0.7)',
                            data: errores
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Predicción de Tipos de CFDI (ML)'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },
        error: function (xhr) {
            alert('Error al obtener predicciones');
            console.error(xhr);
        }
    });
});
