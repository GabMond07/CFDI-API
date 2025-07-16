function loadRegistro() {
    $('#main-content').load('/frontend/view/register.html', function () {
        $('#registroForm').submit(function (e) {
            e.preventDefault();

            const username = $('#username').val().trim();
            const rfc = $('#rfc').val().trim().toUpperCase();
            const email = $('#email').val().trim();
            const password = $('#password').val().trim();

            // Limpiar mensajes previos
            $('#rfcError').text('').hide();
            $('#passwordError').text('').hide();

            let valid = true;

            // Validación RFC
            const rfcRegex = /^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$/i;
            if (!rfcRegex.test(rfc)) {
                $('#rfcError').text('El RFC no tiene un formato válido').show();
                valid = false;
            }

            // Validación Contraseña
            if (password.length < 8) {
                $('#passwordError').text('La contraseña debe tener al menos 8 caracteres').show();
                valid = false;
            }

            if (!valid) return;

            $.ajax({
                url: 'http://localhost:8000/api/v1/auth/register',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ rfc, username, email, password }),
                success: function () {
                    $('#rfcError').hide();
                    $('#passwordError').hide();
                    $('#registroExito').text('Registro exitoso. Ahora puedes iniciar sesión.').show();
                    $('#registroForm')[0].reset();
                },
                error: function (xhr) {
                    let mensaje = 'Error al registrar usuario.';
                    if (xhr.responseJSON && xhr.responseJSON.detail) {
                        mensaje = xhr.responseJSON.detail;
                    }
                    alert(mensaje);  // Puedes cambiar esto si quieres
                }
            });
        });
    });
}

function toggleRegisterPassword() {
  const passwordInput = document.getElementById('password');
  const icon = document.getElementById('toggleRegisterPasswordIcon');

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

