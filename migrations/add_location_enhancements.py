#!/usr/bin/env python3
"""
Migración para mejorar el modelo de ubicaciones:
- Agregar tabla de asociación location_companies
- Agregar nuevos campos al modelo Location
- Hacer company_id opcional
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings
from app.models import Base

def run_migration():
    """Ejecutar la migración"""
    if settings.database_url.startswith("sqlite"):
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Crear tabla de asociación location_companies
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS location_companies (
                location_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                PRIMARY KEY (location_id, company_id),
                FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        """))
        
        # Agregar nuevos campos a la tabla locations
        try:
            conn.execute(text("ALTER TABLE locations ADD COLUMN code VARCHAR(100)"))
        except Exception:
            pass  # Campo ya existe
            
        try:
            conn.execute(text("ALTER TABLE locations ADD COLUMN location_type VARCHAR(20) DEFAULT 'area'"))
        except Exception:
            pass  # Campo ya existe
            
        try:
            conn.execute(text("ALTER TABLE locations ADD COLUMN max_capacity INTEGER"))
        except Exception:
            pass  # Campo ya existe
            
        try:
            conn.execute(text("ALTER TABLE locations ADD COLUMN shelf_count INTEGER"))
        except Exception:
            pass  # Campo ya existe
            
        try:
            conn.execute(text("ALTER TABLE locations ADD COLUMN sort_order INTEGER DEFAULT 0"))
        except Exception:
            pass  # Campo ya existe
        
        # Hacer company_id opcional (remover NOT NULL constraint)
        try:
            # Para SQLite, necesitamos recrear la tabla
            conn.execute(text("""
                CREATE TABLE locations_new AS SELECT * FROM locations
            """))
            
            conn.execute(text("DROP TABLE locations"))
            
            conn.execute(text("""
                CREATE TABLE locations (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    code VARCHAR(100),
                    parent_id INTEGER,
                    location_type VARCHAR(20) DEFAULT 'area',
                    level INTEGER DEFAULT 1,
                    max_capacity INTEGER,
                    shelf_count INTEGER,
                    sort_order INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (parent_id) REFERENCES locations(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """))
            
            conn.execute(text("""
                INSERT INTO locations SELECT * FROM locations_new
            """))
            
            conn.execute(text("DROP TABLE locations_new"))
            
        except Exception as e:
            print(f"Error al modificar company_id: {e}")
        
        conn.commit()
        print("Migración completada exitosamente")

if __name__ == "__main__":
    run_migration()