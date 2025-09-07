# Manual de Usuario - StoraTrack

## Índice
1. [Introducción](#introducción)
2. [Acceso al Sistema](#acceso-al-sistema)
3. [Roles de Usuario](#roles-de-usuario)
4. [Panel de Administración](#panel-de-administración)
5. [Gestión de Empresas](#gestión-de-empresas)
6. [Gestión de Usuarios](#gestión-de-usuarios)
7. [Gestión de Ubicaciones](#gestión-de-ubicaciones)
8. [Gestión de Dispositivos](#gestión-de-dispositivos)
9. [Generación de Etiquetas](#generación-de-etiquetas)
10. [Reportes](#reportes)
11. [Panel de Cliente](#panel-de-cliente)
12. [Solución de Problemas](#solución-de-problemas)

---

## Introducción

StoraTrack es un sistema de gestión de almacenamiento que permite a las empresas rastrear y administrar dispositivos, ubicaciones y generar etiquetas QR para un control eficiente del inventario.

### Características Principales
- **Gestión Multi-empresa**: Soporte para múltiples empresas en una sola instalación
- **Control de Acceso por Roles**: Superadmin, Staff y Cliente con permisos específicos
- **Generación de Etiquetas QR**: Códigos QR y de barras para dispositivos
- **Reportes de Costos**: Análisis detallado de costos de almacenamiento
- **Interfaz Responsive**: Acceso desde cualquier dispositivo

---

## Acceso al Sistema

### URL de Acceso
```
http://localhost:4011
```

### Credenciales por Defecto

**Superadmin:**
- Email: `admin@storatrack.com`
- Contraseña: `admin123`

**Staff:**
- Email: `staff@demo.com`
- Contraseña: `staff123`

**Cliente:**
- Email: `cliente@demo.com`
- Contraseña: `cliente123`

### Proceso de Login
1. Acceder a la URL del sistema
2. Introducir email y contraseña
3. Hacer clic en "Iniciar Sesión"
4. El sistema redirigirá al dashboard correspondiente según el rol

---

## Roles de Usuario

### Superadmin
- **Permisos completos** en todo el sistema
- Gestión de todas las empresas
- Creación y gestión de usuarios staff
- Acceso a todas las funcionalidades

### Staff
- **Permisos administrativos** con algunas restricciones
- Gestión de empresas (crear, editar, eliminar)
- Gestión de usuarios cliente
- Gestión de dispositivos y ubicaciones
- **No puede**: Crear superadmins o eliminar otros staff

### Cliente
- **Acceso limitado** a su empresa asignada
- Visualización de dispositivos de su empresa
- Generación de reportes de su empresa
- **No puede**: Gestionar usuarios, empresas o ubicaciones

---

## Panel de Administración

### Dashboard Principal
El dashboard muestra:
- **Estadísticas generales**: Total de empresas, usuarios, dispositivos
- **Gráficos de actividad**: Dispositivos por estado, distribución por empresa
- **Accesos rápidos**: Enlaces a las funciones más utilizadas

### Navegación
El menú lateral incluye:
- 📊 **Dashboard**: Página principal
- 🏢 **Empresas**: Gestión de empresas
- 👥 **Usuarios**: Gestión de usuarios
- 📍 **Ubicaciones**: Gestión de ubicaciones
- 📱 **Dispositivos**: Gestión de dispositivos
- 🏷️ **Etiquetas**: Generación de etiquetas
- 📈 **Reportes**: Análisis y reportes
- ⚙️ **Configuración**: Ajustes del sistema

---

## Gestión de Empresas

### Crear Nueva Empresa
1. Ir a **Empresas** en el menú lateral
2. Hacer clic en **"+ Nueva Empresa"**
3. Completar el formulario:
   - **Nombre**: Nombre de la empresa
   - **Dirección**: Dirección física
   - **Teléfono**: Número de contacto
   - **Email**: Email de contacto
4. Hacer clic en **"Crear Empresa"**

### Editar Empresa
1. En la lista de empresas, hacer clic en el ícono de edición ✏️
2. Modificar los campos necesarios
3. Hacer clic en **"Actualizar Empresa"**

### Eliminar Empresa
1. En la lista de empresas, hacer clic en el ícono de eliminación 🗑️
2. Confirmar la eliminación en el diálogo
3. **Nota**: Solo se pueden eliminar empresas sin dispositivos asociados

---

## Gestión de Usuarios

### Crear Nuevo Usuario
1. Ir a **Usuarios** en el menú lateral
2. Hacer clic en **"+ Nuevo Usuario"**
3. Completar el formulario:
   - **Email**: Email único del usuario
   - **Nombre Completo**: Nombre y apellido
   - **Contraseña**: Contraseña segura
   - **Rol**: Seleccionar entre Staff o Cliente
   - **Empresa**: (Solo para clientes) Empresa asignada
4. Hacer clic en **"Crear Usuario"**

### Cambiar Rol de Usuario
1. En la lista de usuarios, hacer clic en el menú desplegable del rol
2. Seleccionar el nuevo rol
3. Confirmar el cambio

### Activar/Desactivar Usuario
1. En la lista de usuarios, hacer clic en el botón de estado
2. Confirmar la acción
3. Los usuarios desactivados no pueden acceder al sistema

---

## Gestión de Ubicaciones

### Crear Nueva Ubicación
1. Ir a **Ubicaciones** en el menú lateral
2. Hacer clic en **"+ Nueva Ubicación"**
3. Completar el formulario:
   - **Nombre**: Nombre descriptivo de la ubicación
   - **Empresa**: Empresa propietaria
   - **Tipo**: Seleccionar tipo de ubicación
   - **Descripción**: Descripción adicional (opcional)
4. Hacer clic en **"Crear Ubicación"**

### Tipos de Ubicación
- **Almacén**: Ubicaciones de almacenamiento principal
- **Oficina**: Espacios de oficina
- **Depósito**: Áreas de depósito temporal
- **Otro**: Ubicaciones personalizadas

---

## Gestión de Dispositivos

### Registrar Nuevo Dispositivo
1. Ir a **Dispositivos** en el menú lateral
2. Hacer clic en **"+ Nuevo Dispositivo"**
3. Completar el formulario:
   - **Nombre**: Nombre del dispositivo
   - **Empresa**: Empresa propietaria
   - **Ubicación**: Ubicación actual
   - **Estado**: Estado inicial del dispositivo
   - **Descripción**: Descripción detallada
   - **Valor**: Valor monetario del dispositivo
4. Hacer clic en **"Registrar Dispositivo"**

### Estados de Dispositivo
- **Ingresado**: Recién ingresado al sistema
- **Esperando Recibir**: En tránsito hacia el almacén
- **Almacenado**: Almacenado en ubicación
- **Enviado**: Enviado desde el almacén
- **Retirado**: Retirado del sistema

### Actualizar Estado
1. En la lista de dispositivos, hacer clic en el dispositivo
2. En la vista de detalle, seleccionar nuevo estado
3. Agregar comentarios si es necesario
4. Hacer clic en **"Actualizar Estado"**

---

## Generación de Etiquetas

### Acceso a Generación de Etiquetas
1. Ir a **Etiquetas** en el menú lateral
2. Seleccionar el tipo de etiqueta a generar

### Generar Etiqueta de Dispositivo
1. En la pestaña **"Dispositivos"**
2. Seleccionar dispositivo del menú desplegable
3. Elegir tipo de etiqueta:
   - **Etiqueta Completa**: Incluye QR, código de barras y detalles
   - **Solo QR**: Solo código QR
   - **Solo Código de Barras**: Solo código de barras
4. Hacer clic en **"Generar Etiqueta"**
5. La etiqueta se abrirá en una nueva ventana para imprimir

### Generar Etiquetas de Ubicación
1. En la pestaña **"Ubicaciones"**
2. Seleccionar ubicación del menú desplegable
3. Hacer clic en **"Generar Etiqueta"**
4. Imprimir la etiqueta generada

### Generar Etiquetas por Lote
1. En la pestaña **"Lote"**
2. Seleccionar empresa
3. Elegir filtros (ubicación, estado, etc.)
4. Hacer clic en **"Generar Lote"**
5. Se generará un PDF con todas las etiquetas

---

## Reportes

### Reporte de Costos
1. Ir a **Reportes** en el menú lateral
2. Seleccionar **"Reporte de Costos"**
3. Configurar filtros:
   - **Empresa**: Empresa específica o todas
   - **Período**: Rango de fechas
   - **Ubicación**: Ubicación específica (opcional)
4. Hacer clic en **"Generar Reporte"**
5. El reporte mostrará:
   - Costos por dispositivo
   - Costos por ubicación
   - Totales por período
   - Gráficos de distribución

### Exportar Reportes
1. Una vez generado el reporte
2. Hacer clic en **"Exportar PDF"** o **"Exportar Excel"**
3. El archivo se descargará automáticamente

---

## Panel de Cliente

### Dashboard de Cliente
Los usuarios cliente ven:
- **Dispositivos de su empresa**: Lista filtrada automáticamente
- **Estadísticas limitadas**: Solo de su empresa
- **Reportes restringidos**: Solo de sus dispositivos

### Funcionalidades Disponibles
- ✅ Ver dispositivos de su empresa
- ✅ Generar reportes de costos
- ✅ Descargar etiquetas de sus dispositivos
- ❌ Gestionar usuarios
- ❌ Crear/editar empresas
- ❌ Gestionar ubicaciones

---

## Solución de Problemas

### Problemas Comunes

#### No puedo acceder al sistema
**Solución:**
1. Verificar que el servidor esté ejecutándose
2. Comprobar la URL de acceso
3. Verificar credenciales de usuario
4. Contactar al administrador si el usuario está desactivado

#### No aparecen las ubicaciones en el selector
**Solución:**
1. Verificar que existan ubicaciones creadas
2. Comprobar que el usuario tenga permisos para ver la empresa
3. Actualizar la página (F5)

#### Error al generar etiquetas
**Solución:**
1. Verificar que el dispositivo/ubicación exista
2. Comprobar conexión a internet
3. Intentar con otro navegador
4. Contactar soporte técnico

#### Los reportes no muestran datos
**Solución:**
1. Verificar que existan dispositivos en el período seleccionado
2. Comprobar filtros aplicados
3. Verificar permisos de acceso a la empresa

### Contacto de Soporte

Para problemas técnicos o consultas:
- **Email**: soporte@storatrack.com
- **Teléfono**: +598 XXXX-XXXX
- **Horario**: Lunes a Viernes, 9:00 - 18:00

---

## Información Técnica

### Requisitos del Sistema
- **Navegador**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Resolución**: Mínimo 1024x768
- **Conexión**: Internet estable para funcionalidades en línea

### Seguridad
- Las contraseñas deben tener al menos 8 caracteres
- Se recomienda cambiar contraseñas por defecto
- Las sesiones expiran automáticamente por inactividad
- Todos los datos se almacenan de forma segura

### Actualizaciones
El sistema se actualiza automáticamente. Los usuarios serán notificados de nuevas funcionalidades a través del dashboard.

---

**Versión del Manual**: 1.0  
**Fecha de Actualización**: Enero 2025  
**Sistema**: StoraTrack v1.0