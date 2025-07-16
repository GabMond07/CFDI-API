document.addEventListener('DOMContentLoaded', function () {
  const logoutBtn = document.getElementById('logoutBtn');

  if (logoutBtn) {
    logoutBtn.addEventListener('click', function (e) {
      e.preventDefault();

      const confirmLogout = confirm('¿Estás seguro que deseas cerrar sesión?');

      if (confirmLogout) {
        const token = localStorage.getItem('token');

        // Llamada al endpoint de logout (AJAX)
        fetch('http://localhost:8000/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        })
        .then(response => {
          // Si el servidor responde bien o no, cerramos sesión igual
          localStorage.removeItem('token');
          localStorage.clear();
          loadLogin();
        })
        .catch(error => {
          console.error('Error al cerrar sesión:', error);
          // Aun con error, cerramos localmente
          localStorage.removeItem('token');
          localStorage.clear();
          loadLogin();
        });
      }
    });
  }
});

