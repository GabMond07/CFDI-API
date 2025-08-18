$(document).ready(function () {
    const vistas = {
        dashboard: "dashboard.html",
        subir: "subirCFDI.html",
        consulta: "consultarCFDI.html",
        detalle: "detalleCFDI.html",
        clasificacion: "clasificaciónCFDI.html"
    };

    $("a.nav-link").on("click", function (e) {
        e.preventDefault();
        const idVista = $(this).attr("href").replace("#", "");

        if (vistas[idVista]) {
            cargarVista(idVista);
        } else {
            console.error("Vista no encontrada:", idVista);
        }
    });

    function cargarVista(idVista) {
        const archivo = "view/" + vistas[idVista];
        $("#main-content").load(archivo, function (response, status, xhr) {
            if (status === "error") {
                $("#main-content").html("<div class='alert alert-danger'>Error al cargar la vista.</div>");
                console.error("Error cargando", archivo, xhr.status, xhr.statusText);
            }
        });
    }

    // Exportar función global si la necesitas en otros scripts
    window.cargarVista = cargarVista;
});

