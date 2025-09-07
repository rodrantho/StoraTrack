from app.database import SessionLocal
from sqlalchemy import text

def fix_location_types():
    db = SessionLocal()
    try:
        # Actualizar valores incorrectos en la base de datos
        result = db.execute(text("UPDATE locations SET location_type = 'ESTANTERIA' WHERE location_type = 'estanteria'"))
        print(f"Updated {result.rowcount} rows with 'estanteria' to 'ESTANTERIA'")
        
        result = db.execute(text("UPDATE locations SET location_type = 'DEPOSITO' WHERE location_type = 'deposito'"))
        print(f"Updated {result.rowcount} rows with 'deposito' to 'DEPOSITO'")
        
        result = db.execute(text("UPDATE locations SET location_type = 'ESTANTE' WHERE location_type = 'estante'"))
        print(f"Updated {result.rowcount} rows with 'estante' to 'ESTANTE'")
        
        result = db.execute(text("UPDATE locations SET location_type = 'CAJA' WHERE location_type = 'caja'"))
        print(f"Updated {result.rowcount} rows with 'caja' to 'CAJA'")
        
        result = db.execute(text("UPDATE locations SET location_type = 'AREA' WHERE location_type = 'area'"))
        print(f"Updated {result.rowcount} rows with 'area' to 'AREA'")
        
        db.commit()
        print("All location types updated successfully!")
        
        # Verificar los valores actuales
        result = db.execute(text("SELECT DISTINCT location_type FROM locations"))
        current_types = [row[0] for row in result]
        print(f"Current location types in database: {current_types}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_location_types()