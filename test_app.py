#!/usr/bin/env python3
"""
Script de testing automatizado para StoraTrack
Prueba todas las funcionalidades CRUD y operaciones principales
"""

import requests
import json
import time
from datetime import datetime

class StoraTrackTester:
    def __init__(self, base_url="http://localhost:4011"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_data = {
            "users": [],
            "companies": [],
            "locations": [],
            "devices": []
        }
        
    def log(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def login_as_admin(self):
        """Login como administrador"""
        self.log("Iniciando sesión como administrador...")
        
        # Primero obtener la página de login para establecer cookies
        login_page = self.session.get(f"{self.base_url}/auth/login")
        if login_page.status_code != 200:
            self.log(f"✗ Error accediendo a página de login: {login_page.status_code}", "ERROR")
            return False
            
        login_data = {
            "email": "rodrantho@outlook.com",
            "password": "Kernel1.0"
        }
        
        response = self.session.post(f"{self.base_url}/auth/login", data=login_data, allow_redirects=False)
        
        # Verificar si hay redirección (login exitoso)
        if response.status_code == 302:
            self.log("✓ Login exitoso como administrador")
            return True
        elif response.status_code == 200:
            # Login falló, probablemente credenciales incorrectas
            self.log("✗ Error en login: credenciales incorrectas o página de error", "ERROR")
            if "error" in response.text.lower() or "incorrect" in response.text.lower():
                self.log("✗ Credenciales incorrectas detectadas en la respuesta", "ERROR")
            return False
        else:
            self.log(f"✗ Error inesperado en login: {response.status_code}", "ERROR")
            return False
            
    def create_test_staff_user(self):
        """Crear usuario staff de prueba"""
        self.log("Creando usuario staff de prueba...")
        user_data = {
            "email": "staff_test@storatrack.com",
            "password": "test123456",
            "full_name": "Staff de Prueba",
            "role": "staff",
            "company_id": ""
        }
        
        response = self.session.post(f"{self.base_url}/admin/users/create", data=user_data)
        if response.status_code == 302:  # Redirect after creation
            self.log("✓ Usuario staff creado exitosamente")
            self.test_data["users"].append(user_data)
            return True
        else:
            self.log(f"✗ Error creando usuario staff: {response.status_code}", "ERROR")
            return False
            
    def create_test_company(self):
        """Crear empresa de prueba"""
        self.log("Creando empresa de prueba...")
        company_data = {
            "name": "Empresa Test CRUD",
            "rut": "12345678-9",
            "address": "Dirección de Prueba 123",
            "phone": "+56912345678",
            "email": "test@empresatest.com",
            "contact_person": "Contacto de Prueba",
            "is_active": True
        }
        
        response = self.session.post(f"{self.base_url}/admin/companies/create", data=company_data)
        if response.status_code == 302:
            self.log("✓ Empresa de prueba creada exitosamente")
            self.test_data["companies"].append(company_data)
            return True
        else:
            self.log(f"✗ Error creando empresa: {response.status_code}", "ERROR")
            return False
            
    def create_test_locations(self):
        """Crear ubicaciones de prueba"""
        self.log("Creando ubicaciones de prueba...")
        
        # Ubicación principal
        location_data = {
            "name": "Bodega Principal Test",
            "code": "BPT001",
            "description": "Bodega principal para testing",
            "location_type": "DEPOSITO",
            "company_id": 1,
            "parent_id": "",
            "sort_order": 1,
            "max_capacity": 1000,
            "shelf_count": 10,
            "is_active": True
        }
        
        response = self.session.post(f"{self.base_url}/admin/locations", json=location_data)
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            if result.get("success"):
                self.log("✓ Ubicación principal creada exitosamente")
                self.test_data["locations"].append(location_data)
                location_id = result.get("location_id", 1)
                
                # Crear sub-ubicación
                sub_location_data = {
                    "name": "Estante A1 Test",
                    "code": "EA1T001",
                    "description": "Estante A1 para testing",
                    "location_type": "ESTANTE",
                    "company_id": 1,
                    "parent_id": location_id,
                    "sort_order": 1,
                    "max_capacity": 50,
                    "shelf_count": 1,
                    "is_active": True
                }
                
                response = self.session.post(f"{self.base_url}/admin/locations", json=sub_location_data)
                if response.status_code == 200 or response.status_code == 201:
                    result = response.json()
                    if result.get("success"):
                        self.log("✓ Sub-ubicación creada exitosamente")
                        self.test_data["locations"].append(sub_location_data)
                        return True
                    else:
                        self.log(f"✗ Error creando sub-ubicación: {result.get('message')}", "ERROR")
                        return False
                else:
                    self.log(f"✗ Error creando sub-ubicación: {response.status_code}", "ERROR")
                    return False
            else:
                self.log(f"✗ Error creando ubicación principal: {result.get('message')}", "ERROR")
                return False
        else:
            self.log(f"✗ Error creando ubicación principal: {response.status_code}", "ERROR")
            return False
            
    def create_test_devices(self):
        """Crear dispositivos de prueba"""
        self.log("Creando dispositivos de prueba...")
        
        devices = [
            {
                "name": "Laptop Test 1",
                "serial_number": "TEST001",
                "brand": "TestBrand",
                "model": "TestModel1",
                "device_type": "laptop",
                "company_id": 1,
                "location_id": 1,
                "status": "almacenado",
                "description": "Dispositivo de prueba 1",
                "purchase_date": "2024-01-15",
                "warranty_expiry": "2025-01-15",
                "costo_base": 500000,
                "costo_diario": 1000
            },
            {
                "name": "Desktop Test 2",
                "serial_number": "TEST002",
                "brand": "TestBrand",
                "model": "TestModel2",
                "device_type": "desktop",
                "company_id": 1,
                "location_id": 2,
                "status": "ingresado",
                "description": "Dispositivo de prueba 2",
                "purchase_date": "2024-02-15",
                "warranty_expiry": "2025-02-15",
                "costo_base": 800000,
                "costo_diario": 1500
            }
        ]
        
        created_count = 0
        for device_data in devices:
            response = self.session.post(f"{self.base_url}/admin/devices", json=device_data)
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                if result.get("success"):
                    self.log(f"✓ Dispositivo {device_data['serial_number']} creado exitosamente")
                    self.test_data["devices"].append(device_data)
                    created_count += 1
                else:
                    self.log(f"✗ Error creando dispositivo {device_data['serial_number']}: {result.get('message')}", "ERROR")
            else:
                self.log(f"✗ Error creando dispositivo {device_data['serial_number']}: {response.status_code}", "ERROR")
                
        return created_count == len(devices)
        
    def create_test_client_users(self):
        """Crear usuarios cliente de prueba"""
        self.log("Creando usuarios cliente de prueba...")
        
        client_users = [
            {
                "username": "cliente1_test",
                "email": "cliente1_test@storatrack.com",
                "password": "test123",
                "full_name": "Cliente Test 1",
                "role": "CLIENT",
                "company_id": 1
            },
            {
                "username": "cliente2_test",
                "email": "cliente2_test@storatrack.com",
                "password": "test123",
                "full_name": "Cliente Test 2",
                "role": "CLIENT",
                "company_id": 1
            }
        ]
        
        created_count = 0
        for user_data in client_users:
            response = self.session.post(f"{self.base_url}/admin/users/create", data=user_data)
            if response.status_code == 302:  # Redirección exitosa
                self.log(f"✓ Usuario cliente {user_data['email']} creado exitosamente")
                self.test_data["users"].append(user_data)
                created_count += 1
            elif response.status_code == 200:
                # Verificar si hay error en la URL de redirección
                if "error=" in response.url:
                    self.log(f"✗ Error creando usuario cliente {user_data['email']}: {response.url}", "ERROR")
                else:
                    self.log(f"✓ Usuario cliente {user_data['email']} creado exitosamente")
                    self.test_data["users"].append(user_data)
                    created_count += 1
            else:
                self.log(f"✗ Error creando usuario cliente {user_data['email']}: {response.status_code}", "ERROR")
                
        return created_count == len(client_users)
        
    def test_client_access(self):
        """Probar acceso de usuarios cliente"""
        self.log("Probando acceso de usuarios cliente...")
        
        # Crear nueva sesión para cliente
        client_session = requests.Session()
        
        login_data = {
            "email": "cliente1_test@storatrack.com",
            "password": "test123456"
        }
        
        response = client_session.post(f"{self.base_url}/auth/login", data=login_data)
        if response.status_code == 302:
            self.log("✓ Login cliente exitoso")
            
            # Probar acceso al dashboard cliente
            response = client_session.get(f"{self.base_url}/client/dashboard")
            if response.status_code == 200:
                self.log("✓ Acceso al dashboard cliente exitoso")
                
                # Probar acceso a dispositivos
                response = client_session.get(f"{self.base_url}/client/devices")
                if response.status_code == 200:
                    self.log("✓ Acceso a dispositivos cliente exitoso")
                    return True
                else:
                    self.log(f"✗ Error accediendo a dispositivos cliente: {response.status_code}", "ERROR")
            else:
                self.log(f"✗ Error accediendo al dashboard cliente: {response.status_code}", "ERROR")
        else:
            self.log(f"✗ Error en login cliente: {response.status_code}", "ERROR")
            
        return False
        
    def test_crud_operations(self):
        """Probar operaciones CRUD básicas"""
        self.log("Iniciando pruebas CRUD...")
        
        # Probar acceso a páginas principales
        pages_to_test = [
            "/admin/dashboard",
            "/admin/companies",
            "/admin/locations",
            "/admin/devices",
            "/admin/users"
        ]
        
        for page in pages_to_test:
            response = self.session.get(f"{self.base_url}{page}")
            if response.status_code == 200:
                self.log(f"✓ Acceso a {page} exitoso")
            else:
                self.log(f"✗ Error accediendo a {page}: {response.status_code}", "ERROR")
                
    def cleanup_test_data(self):
        """Limpiar datos de prueba (opcional)"""
        self.log("Limpieza de datos de prueba completada (manual)")
        self.log("Para limpiar manualmente:")
        self.log("- Eliminar usuarios: staff_test@storatrack.com, cliente1_test@storatrack.com, cliente2_test@storatrack.com")
        self.log("- Eliminar empresa: Empresa Test CRUD")
        self.log("- Eliminar ubicaciones: Bodega Principal Test, Estante A1 Test")
        self.log("- Eliminar dispositivos: TEST001, TEST002")
        
    def run_full_test(self):
        """Ejecutar suite completa de pruebas"""
        self.log("=== INICIANDO SUITE DE PRUEBAS STORATRACK ===")
        
        # Login inicial
        if not self.login_as_admin():
            self.log("No se pudo hacer login como admin. Abortando pruebas.", "ERROR")
            return False
            
        # Esperar un poco entre operaciones
        time.sleep(1)
        
        # Crear datos de prueba
        tests = [
            ("Usuario Staff", self.create_test_staff_user),
            ("Empresa", self.create_test_company),
            ("Ubicaciones", self.create_test_locations),
            ("Dispositivos", self.create_test_devices),
            ("Usuarios Cliente", self.create_test_client_users)
        ]
        
        success_count = 0
        for test_name, test_func in tests:
            self.log(f"\n--- Probando {test_name} ---")
            if test_func():
                success_count += 1
            time.sleep(1)  # Pausa entre pruebas
            
        # Probar operaciones CRUD
        self.log("\n--- Probando Operaciones CRUD ---")
        self.test_crud_operations()
        
        # Probar acceso cliente
        self.log("\n--- Probando Acceso Cliente ---")
        if self.test_client_access():
            success_count += 1
            
        # Resumen
        self.log(f"\n=== RESUMEN DE PRUEBAS ===")
        self.log(f"Pruebas exitosas: {success_count}/{len(tests) + 1}")
        
        if success_count == len(tests) + 1:
            self.log("🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        else:
            self.log("⚠️  ALGUNAS PRUEBAS FALLARON - Revisar logs arriba", "WARNING")
            
        # Información de limpieza
        self.log("\n--- Información de Limpieza ---")
        self.cleanup_test_data()
        
        return success_count == len(tests) + 1

if __name__ == "__main__":
    print("StoraTrack - Script de Testing Automatizado")
    print("============================================")
    
    tester = StoraTrackTester()
    success = tester.run_full_test()
    
    if success:
        print("\n✅ Testing completado exitosamente")
    else:
        print("\n❌ Testing completado con errores")
        print("Revisar los logs arriba para más detalles")