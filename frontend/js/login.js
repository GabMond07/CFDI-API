function loadLogin() {
    $('#main-content').load('/frontend/view/login.html', function () {
        $('#loginForm').submit(function (e) {
            e.preventDefault();
            const rfc = $('#rfc').val();
            const password = $('#password').val();

            $.ajax({
                url: 'http://localhost:8000/api/v1/auth/login',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ rfc, password }),
                success: function (response) {
                    localStorage.setItem('token', response.access_token);
                    loadDashboard();
                },
                error: function () {
                    $('#error').text('RFC o contraseña incorrectos').show();
                }
            });
        });
    });
}
