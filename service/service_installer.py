"""
FaceLock Service Installer - Version Robuste (HandleCommandLine)
Usage:
    python service_installer.py install
    python service_installer.py remove
    python service_installer.py start
    python service_installer.py stop
    python service_installer.py debug  # Pour tester en mode console
"""
import sys
import os

# Ajouter le dossier courant au path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"📂 Chemin: {current_dir}")

# Importer le service
try:
    from FaceRecognitionService import FaceLockService
    print("✅ FaceRecognitionService importé")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

if __name__ == '__main__':
    # HandleCommandLine gère automatiquement: install, remove, start, stop, debug
    # Il suffit de passer la classe du service
    import win32serviceutil
    
    print(f"🔧 Commande: {sys.argv[1:] if len(sys.argv) > 1 else '[aucune]'}")
    
    try:
        win32serviceutil.HandleCommandLine(FaceLockService)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\n💡 Essayez avec plus de détails:")
        print("   python service_installer.py install --debug")
        sys.exit(1)