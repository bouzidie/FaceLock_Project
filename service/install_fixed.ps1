# install_fixed.ps1
$PYTHON_EXE = "C:\Users\DELL\Desktop\FaceLock_Project\venv\Scripts\python.exe"
$SCRIPT_PATH = "C:\Users\DELL\Desktop\FaceLock_Project\service\FaceRecognitionService.py"
$SVC_NAME = "FaceLockService"
$SVC_DISPLAY = "FaceLock Biometric Service"

# Nettoyer si existe déjà
sc.exe delete $SVC_NAME 2>$null

# Créer le service avec le bon interpréteur
sc.exe create $SVC_NAME binPath= "`"$PYTHON_EXE` `"$SCRIPT_PATH`"" start= auto DisplayName= "$SVC_DISPLAY"
sc.exe description $SVC_NAME "Authentification biométrique faciale"

Write-Host "✅ Service configuré avec succès" -ForegroundColor Green