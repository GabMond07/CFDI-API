function loadDashboard() {
    $('#main-content').load('view/dashboard.html', function () {
        $('#logoutBtn').click(function () {
            localStorage.removeItem('token');
            loadLogin();
        });

        $('#nav-consultar').click(function () {
            $('#dashboard-content').load('view/consultar_cfdi.html');
        });
    });
}
