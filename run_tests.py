import unittest
import sys
import os

def run_tests():
    """Führt alle Tests aus und gibt das Ergebnis zurück."""
    # Testverzeichnis zum Python-Pfad hinzufügen
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Test Suite erstellen
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='tests', pattern='test_*.py')
    
    # Tests ausführen
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 