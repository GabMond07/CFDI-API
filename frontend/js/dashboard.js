function loadDashboard() {
    $('#main-content').load('view/dashboard.html', function () {
        // Botón de cerrar sesión
        $('#logoutBtn').click(function () {
            localStorage.removeItem('token'); // Elimina el token del localStorage
            loadLogin(); // Carga la pantalla de login
        });

        // Botón "Consultar CFDI"
        $('#nav-consultar').click(function () {
            $('#dashboard-content').load('view/consultarCFDI.html'); // Carga el archivo consultarCFDI.html
        });

        // Botón "Detalle CFDI"
        $('#nav-detalle').click(function () {
            $('#dashboard-content').load('view/detalleCFDI.html'); // Carga el archivo consultarCFDI.html
        });

        // Botón "Clasificacion CFDI"
        $('#nav-clasificacion').click(function () {
            $('#dashboard-content').load('view/clasificacionCFDI.html'); // Carga el archivo consultarCFDI.html
        });

        // Botón "Subir CFDI"
        $('#nav-subir').click(function () {
            $('#dashboard-content').load('view/subirCFDI.html'); // Carga el archivo consultarCFDI.html
        });

        // Botón "Dashboard"
        $('#nav-dashboard').click(function () {
            $('#dashboard-content').html('<h3>Bienvenido al sistema</h3>'); // Muestra mensaje de bienvenida
        });
    });
}
