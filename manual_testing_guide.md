# Guía de Testing Manual - StoraTrack

## Datos de Prueba Creados

### Credenciales de Acceso
- **Superadmin**: rodrantho@outlook.com / Kernel1.0
- **Staff**: staff_test@storatrack.com / test123456
- **Cliente 1**: cliente1_test@storatrack.com / test123456
- **Cliente 2**: cliente2_test@storatrack.com / test123456

### Empresa de Prueba
- **Nombre**: Empresa Test CRUD
- **RUT**: 12345678-9
- **Email**: test@empresatest.com

### Ubicaciones Creadas
1. **Bodega Principal Test** (BPT001) - Tipo: DEPOSITO
2. **Estante A1 Test** (EA1T001) - Tipo: ESTANTE
3. **Estante B2 Test** (EB2T001) - Tipo: ESTANTE

### Dispositivos Creados
1. **Laptop Test 001** (TEST001) - Estado: ALMACENADO
2. **Desktop Test 002** (TEST002) - Estado: INGRESADO
3. **Tablet Test 003** (TEST003) - Estado: ESPERANDO_RECIBIR

## Plan de Testing Manual

### 1. Testing con Usuario Staff

#### Acceso:
1. Ir a: http://localhost:4011/auth/login
2. Ingresar: staff_test@storatrack.com / test123456
3. Verificar redirección a dashboard de admin

#### Testing CRUD Empresas:
1. Ir a: http://localhost:4011/admin/companies
2. **Crear**: Crear nueva empresa "Test Company 2"
3. **Leer**: Verificar que aparece en la lista
4. **Editar**: Modificar nombre a "Test Company 2 Editada"
5. **Eliminar**: Eliminar la empresa creada
6. **Verificar**: Confirmar que "Empresa Test CRUD" sigue existiendo

#### Testing CRUD Ubicaciones:
1. Ir a: http://localhost:4011/admin/locations
2. **Crear**: Crear nueva ubicación "Test Location Nueva"
3. **Leer**: Verificar que aparece en la lista junto con las 3 existentes
4. **Editar**: Modificar descripción de la nueva ubicación
5. **Eliminar**: Eliminar la ubicación creada
6. **Verificar**: Confirmar que las 3 ubicaciones originales siguen existiendo

#### Testing CRUD Dispositivos:
1. Ir a: http://localhost:4011/admin/devices
2. **Crear**: Crear nuevo dispositivo "Test Device Nuevo"
3. **Leer**: Verificar que aparece en la lista junto con los 3 existentes
4. **Editar**: Cambiar estado y ubicación del nuevo dispositivo
5. **Eliminar**: Eliminar el dispositivo creado
6. **Verificar**: Confirmar que los 3 dispositivos originales siguen existiendo

#### Testing CRUD Usuarios:
1. Ir a: http://localhost:4011/admin/users
2. **Crear**: Crear nuevo usuario cliente "test_nuevo@test.com"
3. **Leer**: Verificar que aparece en la lista
4. **Editar**: Modificar nombre completo del usuario
5. **Eliminar**: Eliminar el usuario creado
6. **Verificar**: Confirmar que los usuarios originales siguen existiendo

### 2. Testing con Usuario Cliente

#### Acceso Cliente 1:
1. Cerrar sesión actual
2. Ir a: http://localhost:4011/auth/login
3. Ingresar: cliente1_test@storatrack.com / test123456
4. Verificar redirección a dashboard de cliente

#### Verificaciones Cliente:
1. **Dashboard**: Verificar que solo ve datos de "Empresa Test CRUD"
2. **Dispositivos**: Verificar que puede ver los 3 dispositivos de prueba
3. **Ubicaciones**: Verificar que puede ver las 3 ubicaciones de prueba
4. **Restricciones**: Verificar que NO puede acceder a:
   - /admin/users
   - /admin/companies
   - Datos de otras empresas

#### Acceso Cliente 2:
1. Cerrar sesión
2. Ingresar: cliente2_test@storatrack.com / test123456
3. Repetir las mismas verificaciones que Cliente 1

### 3. Testing de Seguridad y Permisos

#### Verificar Restricciones:
1. **Cliente intentando acceso admin**:
   - Logueado como cliente, intentar ir a /admin/users
   - Debe ser redirigido o mostrar error 403

2. **Acceso sin autenticación**:
   - Cerrar sesión
   - Intentar acceder directamente a /admin/dashboard
   - Debe redirigir a login

3. **Datos aislados por empresa**:
   - Verificar que clientes solo ven datos de su empresa
   - Verificar que no pueden modificar datos de otras empresas

### 4. Testing de Funcionalidades Específicas

#### Movimientos de Dispositivos:
1. Como staff, cambiar ubicación de un dispositivo
2. Verificar que el cambio se refleja correctamente
3. Verificar que los clientes ven la nueva ubicación

#### Estados de Dispositivos:
1. Cambiar estado de dispositivos (INGRESADO → ALMACENADO → ENVIADO)
2. Verificar que los cambios se reflejan en tiempo real

#### Búsquedas y Filtros:
1. Probar búsqueda por serial number
2. Probar filtros por estado
3. Probar filtros por ubicación

## Checklist de Verificación

### ✅ Funcionalidades Básicas
- [ ] Login/Logout funciona correctamente
- [ ] Dashboard muestra información relevante
- [ ] Navegación entre secciones funciona

### ✅ CRUD Empresas (Solo Staff/Admin)
- [ ] Crear empresa nueva
- [ ] Listar empresas existentes
- [ ] Editar empresa existente
- [ ] Eliminar empresa

### ✅ CRUD Ubicaciones
- [ ] Crear ubicación nueva
- [ ] Listar ubicaciones existentes
- [ ] Editar ubicación existente
- [ ] Eliminar ubicación

### ✅ CRUD Dispositivos
- [ ] Crear dispositivo nuevo
- [ ] Listar dispositivos existentes
- [ ] Editar dispositivo existente
- [ ] Eliminar dispositivo
- [ ] Cambiar ubicación de dispositivo
- [ ] Cambiar estado de dispositivo

### ✅ CRUD Usuarios (Solo Staff/Admin)
- [ ] Crear usuario nuevo
- [ ] Listar usuarios existentes
- [ ] Editar usuario existente
- [ ] Eliminar usuario

### ✅ Permisos y Seguridad
- [ ] Staff puede acceder a todas las funciones admin
- [ ] Clientes solo ven datos de su empresa
- [ ] Clientes no pueden acceder a funciones admin
- [ ] Redirección correcta según rol de usuario

### ✅ Acceso de Clientes
- [ ] Cliente 1 puede ver sus dispositivos
- [ ] Cliente 1 puede ver sus ubicaciones
- [ ] Cliente 2 puede ver sus dispositivos
- [ ] Cliente 2 puede ver sus ubicaciones
- [ ] Clientes no ven datos de otras empresas

## URLs de Testing

### Administración (Staff/Admin)
- Dashboard: http://localhost:4011/admin/dashboard
- Usuarios: http://localhost:4011/admin/users
- Empresas: http://localhost:4011/admin/companies
- Ubicaciones: http://localhost:4011/admin/locations
- Dispositivos: http://localhost:4011/admin/devices

### Cliente
- Dashboard: http://localhost:4011/client/dashboard
- Login: http://localhost:4011/auth/login
- Logout: http://localhost:4011/auth/logout

## Comandos de Utilidad

### Limpiar Datos de Prueba
```bash
python create_test_data.py cleanup
```

### Recrear Datos de Prueba
```bash
python create_test_data.py create
```

### Verificar Estado del Servidor
```bash
# El servidor debe estar corriendo en:
http://localhost:4011
```

## Notas Importantes

1. **Siempre probar en orden**: Primero como staff, luego como clientes
2. **Verificar permisos**: Cada rol debe tener acceso solo a lo que corresponde
3. **Datos aislados**: Los clientes solo deben ver datos de su empresa
4. **Funcionalidad completa**: Todas las operaciones CRUD deben funcionar
5. **Interfaz responsiva**: Probar en diferentes tamaños de pantalla

## Problemas Conocidos a Verificar

1. **Errores 404/405**: Verificar que todas las rutas funcionan correctamente
2. **Permisos**: Verificar que los roles se respetan
3. **Datos**: Verificar que los datos se muestran correctamente
4. **Navegación**: Verificar que la navegación es intuitiva

---

**Fecha de creación**: $(date)
**Versión**: 1.0
**Estado**: Datos de prueba creados y listos para testing