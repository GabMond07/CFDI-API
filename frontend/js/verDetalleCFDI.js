$(document).on('click', '.ver-detalle', function () {
    const cfdi = $(this).data('cfdi');

    const contenido = `
        <strong>UUID:</strong> ${cfdi.uuid}<br>
        <strong>Fecha:</strong> ${new Date(cfdi.issue_date).toLocaleString()}<br>
        <strong>Serie:</strong> ${cfdi.serie || ''} <strong>Folio:</strong> ${cfdi.folio || ''}<br>
        <strong>Versión:</strong> ${cfdi.version || ''}<br>
        <strong>Total:</strong> ${cfdi.total} <strong>Subtotal:</strong> ${cfdi.subtotal}<br>
        <strong>Método de Pago:</strong> ${cfdi.payment_method || ''} <strong>Forma de Pago:</strong> ${cfdi.payment_form || ''}<br>
        <strong>Moneda:</strong> ${cfdi.currency || ''}<br>
        <strong>Lugar de expedición:</strong> ${cfdi.place_of_issue || ''}<br>
        <hr>
        <strong><u>Emisor</u></strong><br>
        <strong>RFC:</strong> ${cfdi.issuer?.rfc_issuer || ''}<br>
        <strong>Nombre:</strong> ${cfdi.issuer?.name_issuer || ''}<br>
        <strong>Régimen Fiscal:</strong> ${cfdi.issuer?.tax_regime || ''}<br>
        <hr>
        <strong><u>Receptor</u></strong><br>
        <strong>RFC:</strong> ${cfdi.receiver?.rfc_receiver || ''}<br>
        <strong>Nombre:</strong> ${cfdi.receiver?.name_receiver || ''}<br>
        <strong>Domicilio Fiscal:</strong> ${cfdi.receiver?.tax_address || ''}<br>
        <strong>Uso CFDI:</strong> ${cfdi.receiver?.cfdi_use || ''}<br>
    `;

    $('#detalleContenido').html(contenido);
    $('#detalleModal').modal('show');
});
