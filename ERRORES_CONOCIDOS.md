# Errores Conocidos - StoraTrack

## Error de Comparación de Roles en Templates Jinja2

**Fecha:** Enero 2025
**Ubicación:** Templates que usan comparaciones de roles de usuario
**Severidad:** Media

### Descripción del Problema
Los botones o elementos condicionales que dependen del rol del usuario no aparecen debido a inconsistencias en la comparación de valores de enum entre el backend y los templates.

### Causa Raíz
- En `app/models.py`, el enum `UserRole` define valores en minúsculas:
  ```python
  class UserRole(enum.Enum):
      SUPERADMIN = "superadmin"  # valor en minúsculas
      STAFF = "staff"
      CLIENT_USER = "client_user"
  ```

- En los templates Jinja2, las comparaciones pueden usar valores en mayúsculas por error:
  ```jinja2
  {% if current_user.role.value == 'SUPERADMIN' %}  <!-- INCORRECTO -->
  {% if current_user.role.value == 'superadmin' %}  <!-- CORRECTO -->
  ```

### Síntomas
- Botones de acción no aparecen para usuarios con permisos correctos
- Elementos de UI condicionales no se muestran
- Funcionalidad aparentemente "faltante" en la interfaz

### Solución
Siempre usar los valores exactos del enum en minúsculas en las comparaciones de templates:
- `'superadmin'` en lugar de `'SUPERADMIN'`
- `'staff'` en lugar de `'STAFF'`
- `'client_user'` en lugar de `'CLIENT_USER'`

### Archivos Afectados Conocidos
- `templates/admin/users.html` - Botón de eliminación de usuarios

### Prevención
- Revisar todas las comparaciones de roles en templates
- Considerar crear constantes o helpers para evitar errores de tipeo
- Documentar claramente los valores de enum en comentarios

### Ejemplo de Corrección
```jinja2
<!-- ANTES (incorrecto) -->
{% if current_user.role.value == 'SUPERADMIN' %}

<!-- DESPUÉS (correcto) -->
{% if current_user.role.value == 'superadmin' %}
```