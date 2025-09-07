# Guía Rápida - StoraTrack

## 🚀 Inicio Rápido

### Primer Acceso
1. **Acceder**: `http://localhost:4011`
2. **Login**: `admin@storatrack.com` / `admin123`
3. **Cambiar contraseña** en Perfil → Configuración

### Configuración Inicial (5 minutos)
```
1. Crear primera empresa
2. Crear ubicaciones básicas
3. Registrar primer dispositivo
4. Generar primera etiqueta
```

---

## 📋 Flujos de Trabajo Principales

### Flujo 1: Nueva Empresa
```
Empresas → + Nueva Empresa → Completar datos → Crear
↓
Ubicaciones → + Nueva Ubicación → Asignar empresa → Crear
↓
Usuarios → + Nuevo Usuario → Rol: Cliente → Asignar empresa
```

### Flujo 2: Registro de Dispositivo
```
Dispositivos → + Nuevo Dispositivo
↓
Completar: Nombre, Empresa, Ubicación, Estado
↓
Etiquetas → Dispositivos → Seleccionar → Generar
```

### Flujo 3: Cambio de Estado
```
Dispositivos → Seleccionar dispositivo
↓
Cambiar estado → Agregar comentario → Actualizar
↓
Reportes → Ver historial de cambios
```

---

## ⚡ Atajos de Teclado

| Acción | Atajo |
|--------|-------|
| Buscar | `Ctrl + F` |
| Nueva empresa | `Alt + E` |
| Nuevo usuario | `Alt + U` |
| Nuevo dispositivo | `Alt + D` |
| Generar etiqueta | `Alt + L` |
| Dashboard | `Alt + H` |

---

## 🎯 Casos de Uso Frecuentes

### Caso 1: Empresa Nueva
**Tiempo estimado**: 10 minutos

1. **Crear empresa**
   ```
   Nombre: "Empresa ABC"
   Dirección: "Calle 123, Montevideo"
   Email: "contacto@empresaabc.com"
   ```

2. **Crear ubicaciones**
   ```
   - "Almacén Principal" (Tipo: Almacén)
   - "Oficina Central" (Tipo: Oficina)
   - "Depósito Temporal" (Tipo: Depósito)
   ```

3. **Crear usuario cliente**
   ```
   Email: "admin@empresaabc.com"
   Rol: Cliente
   Empresa: "Empresa ABC"
   ```

### Caso 2: Ingreso Masivo de Dispositivos
**Tiempo estimado**: 5 minutos por dispositivo

1. **Preparar lista de dispositivos**
   ```
   - Laptop Dell XPS 13
   - Monitor Samsung 24"
   - Impresora HP LaserJet
   ```

2. **Registro rápido**
   ```
   Dispositivos → + Nuevo → Completar → Guardar
   (Repetir para cada dispositivo)
   ```

3. **Generar etiquetas en lote**
   ```
   Etiquetas → Lote → Seleccionar empresa → Generar
   ```

### Caso 3: Reporte Mensual
**Tiempo estimado**: 3 minutos

1. **Configurar filtros**
   ```
   Período: Último mes
   Empresa: Todas o específica
   ```

2. **Generar y exportar**
   ```
   Reportes → Costos → Configurar → Generar → Exportar PDF
   ```

---

## 🔧 Configuraciones Recomendadas

### Para Superadmin
```
✅ Crear al menos un usuario staff
✅ Configurar empresa demo para pruebas
✅ Establecer ubicaciones estándar
✅ Definir convenciones de nombres
```

### Para Staff
```
✅ Revisar permisos asignados
✅ Familiarizarse con empresas asignadas
✅ Configurar filtros frecuentes
✅ Establecer rutinas de reportes
```

### Para Cliente
```
✅ Cambiar contraseña inicial
✅ Revisar dispositivos asignados
✅ Configurar notificaciones
✅ Descargar manual de usuario
```

---

## 📊 Métricas Importantes

### Dashboard - Indicadores Clave
- **Total Empresas**: Número de empresas activas
- **Total Usuarios**: Usuarios activos en el sistema
- **Total Dispositivos**: Dispositivos registrados
- **Dispositivos por Estado**: Distribución actual

### Reportes - KPIs
- **Costo por Dispositivo**: Promedio mensual
- **Utilización por Ubicación**: Porcentaje de ocupación
- **Rotación de Dispositivos**: Frecuencia de cambios
- **Tiempo de Almacenamiento**: Promedio por dispositivo

---

## 🚨 Alertas y Notificaciones

### Alertas del Sistema
- 🔴 **Error**: Problemas críticos que requieren atención inmediata
- 🟡 **Advertencia**: Situaciones que requieren revisión
- 🟢 **Éxito**: Confirmación de acciones completadas
- 🔵 **Info**: Información general del sistema

### Notificaciones Automáticas
- Dispositivo sin movimiento por 30 días
- Usuario inactivo por 7 días
- Empresa sin dispositivos registrados
- Ubicación sin asignaciones

---

## 🛠️ Mantenimiento Básico

### Tareas Diarias
- [ ] Revisar alertas del sistema
- [ ] Verificar nuevos registros
- [ ] Comprobar estados de dispositivos

### Tareas Semanales
- [ ] Generar reportes de actividad
- [ ] Revisar usuarios inactivos
- [ ] Limpiar datos temporales

### Tareas Mensuales
- [ ] Backup de base de datos
- [ ] Revisar permisos de usuarios
- [ ] Actualizar documentación
- [ ] Análisis de métricas

---

## 📱 Acceso Móvil

### Navegadores Compatibles
- ✅ Chrome Mobile
- ✅ Safari iOS
- ✅ Firefox Mobile
- ✅ Edge Mobile

### Funcionalidades Móviles
- ✅ Dashboard responsivo
- ✅ Consulta de dispositivos
- ✅ Generación de etiquetas
- ✅ Reportes básicos
- ❌ Gestión de usuarios (recomendado desde desktop)
- ❌ Configuración avanzada

---

## 🔍 Búsqueda Avanzada

### Filtros Disponibles

**Dispositivos:**
```
- Por nombre: "laptop"
- Por empresa: Seleccionar de lista
- Por estado: Almacenado, Enviado, etc.
- Por ubicación: Filtrar por ubicación específica
- Por fecha: Rango de fechas de registro
```

**Usuarios:**
```
- Por nombre: "Juan Pérez"
- Por email: "juan@empresa.com"
- Por rol: Superadmin, Staff, Cliente
- Por empresa: Empresa asignada
- Por estado: Activo/Inactivo
```

### Operadores de Búsqueda
- `"texto exacto"`: Búsqueda exacta
- `texto*`: Búsqueda con comodín
- `campo:valor`: Búsqueda por campo específico

---

## 💡 Consejos y Trucos

### Productividad
1. **Usar filtros guardados** para búsquedas frecuentes
2. **Configurar dashboard** con widgets relevantes
3. **Crear plantillas** de dispositivos comunes
4. **Usar códigos** consistentes para ubicaciones

### Organización
1. **Convenciones de nombres**:
   ```
   Dispositivos: [TIPO]-[MARCA]-[NUMERO]
   Ubicaciones: [EMPRESA]-[AREA]-[DETALLE]
   ```

2. **Estructura de empresas**:
   ```
   Empresa Principal
   ├── Sucursal Norte
   ├── Sucursal Sur
   └── Depósito Central
   ```

### Seguridad
1. **Cambiar contraseñas** regularmente
2. **Revisar permisos** de usuarios periódicamente
3. **Monitorear accesos** inusuales
4. **Backup regular** de datos importantes

---

## 📞 Soporte Rápido

### Problemas Frecuentes - Soluciones Rápidas

| Problema | Solución Rápida |
|----------|----------------|
| No carga la página | F5 o Ctrl+F5 |
| Error de login | Verificar credenciales |
| No aparecen datos | Revisar filtros activos |
| Etiqueta no genera | Verificar datos del dispositivo |
| Reporte vacío | Ajustar rango de fechas |

### Información del Sistema
```
Versión: 1.0
Puerto: 4011
Base de datos: SQLite/PostgreSQL
Framework: FastAPI + Jinja2
```

### Logs de Error
Ubicación: `logs/app.log`
Nivel: INFO, WARNING, ERROR

---

**Última actualización**: Enero 2025  
**Versión de la guía**: 1.0