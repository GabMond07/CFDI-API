function cerrarSesion() {
    localStorage.removeItem("token");
    $("#navbar-auth").hide();
    loadLogin();
}

$(document).on("click", "#cerrarSesion", cerrarSesion);



