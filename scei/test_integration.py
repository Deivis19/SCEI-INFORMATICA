
import os
import sys
import unittest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scei.data.models import Base, Direccion, Equipo, Mantenimiento, User
from scei.data import repositories
from scei.bootstrap import run_bootstrap
from scei.utils import validate_password_strength

class TestFunctional(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("Starting Functional Tests...")
        # Ensure minimal data exists
        try:
            run_bootstrap()
        except ImportError:
            # Fallback if bootstrap isn't importable properly? (Should be fine now)
            pass
        except Exception as e:
            print(f"Warning: Bootstrap failed: {e}")

    def test_01_users(self):
        print("\n[Test] User Authentication")
        # Inject a test user to be sure
        from scei.data.repositories import session_scope
        with session_scope() as s:
            u = s.query(User).filter_by(username="TEST_USER").first()
            if u: s.delete(u)
            s.add(User(username="TEST_USER", password="TestPass123!"))
            
        # Test authenticating with known default user
        self.assertTrue(repositories.check_user("TEST_USER", "TestPass123!"),
                        "Should authenticate test user")
        self.assertFalse(repositories.check_user("TEST_USER", "wrongpass"), "Should reject wrong password")
        
        # Cleanup
        with session_scope() as s:
            u = s.query(User).filter_by(username="TEST_USER").first()
            if u: s.delete(u)
        
    def test_02_password_validation(self):
        print("\n[Test] Password Validation Logic")
        self.assertTrue(validate_password_strength("StrongPass1!"), "Should accept strong password")
        self.assertFalse(validate_password_strength("week"), "Should reject weak password")
        self.assertFalse(validate_password_strength("NoDigits!"), "Should reject no digits")
        self.assertFalse(validate_password_strength("NoSpecial1"), "Should reject no special char")
    
    def test_03_direcciones_crud(self):
        print("\n[Test] Direcciones Repository (CRUD)")
        # Create
        test_dir_name = "TEST_DIRECTION_XYZ"
        existing = [d for d in repositories.list_direcciones() if d.nombre == test_dir_name]
        for e in existing:
            repositories.delete_direccion(e.id)
            
        repositories.add_direccion(test_dir_name)
        dirs = repositories.list_direcciones()
        created = next((d for d in dirs if d.nombre == test_dir_name), None)
        self.assertIsNotNone(created, "Direccion should be created")
        
        # Update
        repositories.update_direccion(created.id, test_dir_name + "_UPDATED", 1)
        updated_list = repositories.list_direcciones()
        updated = next((d for d in updated_list if d.id == created.id), None)
        self.assertEqual(updated.nombre, test_dir_name + "_UPDATED", "Direccion name should be updated")
        
        # Delete
        repositories.delete_direccion(created.id)
        final_list = repositories.list_direcciones()
        deleted = next((d for d in final_list if d.id == created.id), None)
        self.assertIsNone(deleted, "Direccion should be deleted")

    def test_04_equipos_crud(self):
        print("\n[Test] Equipos Repository (CRUD)")
        # Setup: Need a direction first
        rep_dirs = repositories.list_direcciones()
        if not rep_dirs:
            repositories.add_direccion("Temp Dir")
            rep_dirs = repositories.list_direcciones()
        dir_id = rep_dirs[0].id
        
        # Create
        code = "TEST-PC-001"
        data = {
            "codigo_interno": code,
            "descripcion": "Test PC",
            "marca": "Dell",
            "modelo": "Optiplex",
            "nro_serie": "12345",
            "estado": "optimo",
            "direccion_id": dir_id
        }
        
        # Clean previous run
        existing = [e for e in repositories.list_equipos() if e.codigo_interno == code]
        for e in existing:
            repositories.delete_equipo(e.id)
            
        repositories.add_equipo(data)
        
        # List
        eqs = repositories.list_equipos()
        created = next((e for e in eqs if e.codigo_interno == code), None)
        self.assertIsNotNone(created, "Equipo should be created")
        self.assertEqual(created.marca, "Dell")
        
        # Update
        repositories.update_equipo(created.id, {"marca": "HP"})
        updated_eq = repositories.get_equipo(created.id)
        self.assertEqual(updated_eq.marca, "HP", "Marca should be updated")
        
        # List by Direccion
        eqs_by_dir = repositories.list_equipos_by_direccion(dir_id)
        self.assertTrue(any(e.id == created.id for e in eqs_by_dir), "Should find equipo in direction")
        
        # Delete
        repositories.delete_equipo(created.id)
        deleted = repositories.get_equipo(created.id)
        self.assertIsNone(deleted, "Equipo should be deleted")

    def test_05_report_forms(self):
        print("\n[Test] Report Forms Strategy UI")
        # Requires basic QApplication if widgets are instantiated
        from PyQt6.QtWidgets import QApplication
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
            
        from scei.ui.report_forms import EquiposReportForm, MantenimientosReportForm
        
        # Test Equipos Form
        f1 = EquiposReportForm()
        w1 = f1.get_widget()
        self.assertIsNotNone(w1, "Widget should be created")
        vals1 = f1.get_values()
        self.assertIn("codigo", vals1)
        self.assertIn("estado", vals1)
        
        # Test Mantenimientos Form
        f2 = MantenimientosReportForm()
        w2 = f2.get_widget()
        self.assertIsNotNone(w2, "Widget should be created")
        vals2 = f2.get_values()
        self.assertIn("from", vals2)
        self.assertIn("to", vals2)

if __name__ == '__main__':
    unittest.main()
