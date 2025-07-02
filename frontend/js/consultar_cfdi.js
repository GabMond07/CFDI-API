$(document).on('submit', '#formConsultaCFDI', function (e) {
    e.preventDefault();
    const token = localStorage.getItem('token');

    const formDataArray = $(this).serializeArray();
    const filtros = {};

    formDataArray.forEach(field => {
        if (field.value) {
            filtros[field.name] = field.value;
        }
    });

    filtros.pagina = filtros.pagina || 1;
    filtros.por_pagina = filtros.por_pagina || 10;

    const queryString = $.param(filtros);

    $.ajax({
        url: `http://localhost:8000/api/v1/consulta?${queryString}`,
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + token
        },
        success: function (response) {
            const datos = response.datos;
            const $tabla = $('#tablaResultados');
            $tabla.empty();

            if (datos.length === 0) {
                $tabla.append('<tr><td colspan="15" class="text-center">No se encontraron resultados.</td></tr>');
            } else {
                datos.forEach(cfdi => {
                    $('#tablaResultados').append(`
        <tr>
            <td title="${cfdi.uuid}">${cfdi.uuid?.slice(0, 8)}...</td>
                            <td>${cfdi.issue_date ? new Date(cfdi.issue_date).toLocaleString() : ''}</td>
                            <td>${cfdi.serie || ''}</td>
                            <td>${cfdi.folio || ''}</td>
                            <td>${cfdi.version || ''}</td>
                            <td>${cfdi.total?.toFixed(2) || ''}</td>
                            <td>${cfdi.subtotal?.toFixed(2) || ''}</td>
                            <td>${cfdi.payment_method || ''}</td>
                            <td>${cfdi.payment_form || ''}</td>
                            <td>${cfdi.currency || ''}</td>
                            <td title="${cfdi.certificate}">${cfdi.certificate ? cfdi.certificate.slice(0, 10) + '...' : ''}</td>
                            <td>${cfdi.certificate_number || ''}</td>
                            <td>${cfdi.place_of_issue || ''}</td>
                            <td>${cfdi.type || ''}</td>
                            <td title="${cfdi.seal}">${cfdi.seal ? cfdi.seal.slice(0, 10) + '...' : ''}</td>
            <td>
                <button class="btn btn-sm btn-primary ver-detalle" data-cfdi='${JSON.stringify(cfdi)}'>Ver detalle</button>
            </td>
        </tr>
    `);
                });

            }

            $('#resultadoConsulta').show();
        },
        error: function () {
            $('#resultadoConsulta').show();
            $('#tablaResultados').html('<tr><td colspan="15" class="text-center text-danger">Error al consultar CFDI.</td></tr>');
        }
    });
});
