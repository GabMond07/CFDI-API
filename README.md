# Proyecto FastAPI con Prisma

Este proyecto es una API desarrollada con **FastAPI** y **Prisma** para la gestión eficiente de datos. Está diseñado para proporcionar endpoints de exportación e integración de datos, con un enfoque en escalabilidad y mantenibilidad.

## Características principales

- **Framework**: FastAPI para una API asíncrona, rápida y fácil de usar.
- **ORM**: Prisma para la gestión de la base de datos, con soporte para múltiples motores (PostgreSQL, MySQL, SQLite, etc.).
- **Endpoints**: Implementa endpoints para exportación e integración de datos.
- **Autenticación**: Soporte para autenticación mediante JWT (opcional, configurable).
- **Variables de entorno**: Configuración flexible usando archivos `.env`.
- **Documentación automática**: Swagger UI integrado para explorar los endpoints.

## Requisitos previos

- Python 3.8+
- Node.js (para Prisma CLI)
- PostgreSQL
- `pip` y `npm` instalados

## Instalación

1. **Clonar el repositorio**

   ```bash
   git clone <https://github.com/GabMond07/CFDI-API.git>
   cd <CFDI-API>
   ```

2. **Crear un entorno virtual**

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias de Python**

   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar Prisma CLI**
   ```bash
   npm install -g @prisma/cli
   ```

## Configuración de variables de entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
DATABASE_URL="postgresql://usuario:contraseña@localhost:5432/nombre_db"
JWT_SECRET="tu_secreto_para_jwt"
ENVIRONMENT="development"
```

- `DATABASE_URL`: URL de conexión a la base de datos.
- `JWT_SECRET`: Clave secreta para firmar tokens JWT.
- `ENVIRONMENT`: Define el entorno (`development`, `production`, etc.).

## Migración de la base de datos con Prisma

1. **Generar el cliente de Prisma**

   ```bash
   prisma generate
   ```

2. **Aplicar migraciones a la base de datos**

   ```bash
   prisma migrate dev --name init
   ```

   Esto creará las tablas definidas en el archivo `schema.prisma`.

3. **(Opcional) Crear una nueva migración**
   Si modificas `schema.prisma`, ejecuta:
   ```bash
   prisma migrate dev --name nombre_migracion
   ```

## Iniciar el proyecto

1. **Iniciar el servidor con Uvicorn**

   ```bash
   uvicorn src.main:app --reload
   ```

   - El servidor se ejecutará en `http://localhost:8000`.
   - El modo `--reload` habilita la recarga automática en desarrollo.

2. **Acceder a la documentación**
   - Abre `http://localhost:8000/docs` para explorar la API con Swagger UI.

## Estructura del proyecto

````
├── Frontend/             # Frontend de la aplicación (solo consultas)
├── prisma/
│   └── schema.prisma     # Esquema de la base de datos
├── src/
│   ├── event_bus/        # Eventos de la API
|   ├── ml/               # Machine Learning (no implementado al 100%)
│   ├── Models/           # Modelos de datos (Pydantic)
│   ├── router/           # Endpoints de la API
│   ├── service/          # Lógica de negocio
|   ├── auth.py           # Autenticación y autorización
|   ├── database.py       # Inicializa cliente Prisma
|   ├── dependencies.py   # Tenant ID para endpoints (no implementado al 100%)
│   ├── main.py           # Punto de entrada de la API
|   ├── middleware.py     # Middleware para la API
|   ├── permission.py     # Permisos para endpoints (RBAC)
├── .env                  # Variables de entorno (Crear)
├── .gitignore            # Archivos a ignorar
├── cfdv40.xsd            # Esquema de validación de CFDIs (Ejemplo)
├── BD.sql                # Base de datos en formato SQL
├── requirements.txt      # Dependencias de Python
├── script_upload         # Script para cargar CFDIs por lotes
└── README.md             # Este archivo
```<>

## Scripts útiles

- **Formatear el esquema de Prisma**
  ```bash
  prisma format
````

- **Verificar el estado de las migraciones**
  ```bash
  prisma migrate status
  ```

## 🔒 Especificación de Permisos (Columna `permissions`)

La columna `permissions` de la tabla `Roles` utiliza el tipo de dato `jsonb` de PostgreSQL para almacenar una lista de capacidades (`scopes`) que un rol específico puede ejecutar en el sistema. Esto permite una gestión de acceso flexible y escalable.
Se encuntra disponible en el script en la base de datos: `BD.sql`

### Formato JSON

El formato requerido para el objeto JSON es una clave principal llamada `scopes`, que contiene un array de strings. Cada string dentro del array representa un permiso activo.

| Clave    | Tipo          | Descripción                                |
| -------- | ------------- | ------------------------------------------ |
| `scopes` | Array<String> | Lista de permisos disponibles para el rol. |

**Estructura Ejemplo: (Permisos disponibles para el rol "Contribuyente")**

```json
{
  "scopes": ["reports:generate", "write:cfdis", "join:execute"]
}
```

### Permisos Disponibles Actualmente

Los siguientes son los permisos definidos para realizar operaciones en el sistema:

| Permiso            | Descripción                                                                                         |
| ------------------ | --------------------------------------------------------------------------------------------------- |
| `reports:generate` | Permite al usuario generar y descargar reportes del sistema.                                        |
| `write:cfdis`      | Permite al usuario crear y editar registros de Comprobantes Fiscales Digitales por Internet (CFDI). |
| `join:execute`     | Permite al usuario ejecutar operaciones de unión o integración específicas.                         |

## Notas adicionales

- Asegúrate de que la base de datos esté corriendo antes de aplicar migraciones.
- Para entornos de producción, elimina la bandera `--reload` en Uvicorn y configura un servidor como Gunicorn.
- Mantén el archivo `.env` fuera del control de versiones (agregar `.env` a `.gitignore`).
