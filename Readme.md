
# Task Manager API

## Descripción

**Task Manager API** es un servidor RESTful desarrollado en Django y Django REST Framework que permite a los usuarios gestionar proyectos y tareas colaborativas.  
Incluye autenticación JWT, gestión de usuarios, proyectos y tareas, y control de permisos según el rol en cada proyecto.

---

## Funcionalidades principales

- **Registro y login de usuarios**.
- **Creación y gestión de proyectos**:  
  - Nombre, descripción, estado (archivado/no archivado).
  - Solo el jefe (creador) puede editar/eliminar el proyecto.
  - Proyectos archivados: solo consulta de tareas, no se pueden crear/editar/eliminar tareas.
- **Gestión de miembros**:
  - Asociar/desasociar usuarios a proyectos.
  - Si un usuario es removido, sus tareas pasan al jefe del proyecto.
  - Si el jefe es removido, se escoge un nuevo jefe(el primero en la lista d miembros) o se proporciona quien a de ser el jefe
- **Gestión de tareas**:
  - Nombre, estado (pendiente, en progreso, completada), prioridad (baja, media, alta).
  - Solo miembros pueden ser asignados a tareas.
  - Cada usuario puede gestionar (crear, editar, eliminar) sus propias tareas.
  - Los demás miembros solo pueden consultar las tareas de otros.
- **Validaciones y reglas de negocio**:
  - No se pueden crear tareas en proyectos archivados.
  - Solo el jefe puede editar/eliminar proyectos.

---

## Endpoints implementados

- Listar los proyectos del usuario autenticado.
- Crear, editar y eliminar proyectos.
- Listar, crear, editar y eliminar tareas de un proyecto.
- Cambiar estado y prioridad de una tarea.
- Gestión de miembros en proyectos.
- Autenticación JWT (login, refresh).

---

## Tecnologías usadas

- Python 3.12
- Django 4.2
- Django REST Framework
- djangorestframework-simplejwt (autenticación JWT)
- SQLite (persistente en Docker)

---


## Pruebas de la API

Puedes usar **Postman** o cualquier cliente HTTP para probar los endpoints.  
Recuerda siempre autenticarte usando el token JWT en la cabecera:

```
Authorization: Bearer 
```

---

## Buenas prácticas implementadas

- Arquitectura modular.
- Validaciones exhaustivas en modelos y vistas.
- Uso de permisos y autenticación JWT.
- Código documentado y limpio.
- Proyecto dockerizado para fácil despliegue.

---

## Repositorio

El código está disponible en el siguiente repositorio público de GitHub:  
[https://github.com/tuusuario/task-manager-api](https://github.com/tuusuario/task-manager-api)
