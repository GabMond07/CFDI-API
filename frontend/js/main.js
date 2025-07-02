$(document).ready(function () {
    const token = localStorage.getItem('token');

    if (token) {
        loadDashboard();
    } else {
        loadLogin();
    }
});
