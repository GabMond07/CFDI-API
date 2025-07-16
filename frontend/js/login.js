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

function togglePassword() {
    const passwordInput = document.getElementById('password');
    const icon = document.getElementById('togglePasswordIcon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('bi-eye-fill');
        icon.classList.add('bi-eye-slash-fill');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('bi-eye-slash-fill');
        icon.classList.add('bi-eye-fill');
    }
}
