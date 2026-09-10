@echo off
echo ==========================================
echo   Creation de l'environnement virtuel
echo ==========================================

REM Verifie si le dossier .venv existe deja
if exist .venv\ (
    echo L'environnement virtuel ".venv" existe deja.
) else (
    echo Creation en cours, cela peut prendre quelques secondes...
    python -m venv .venv
    
    if errorlevel 1 (
        echo [Erreur] Python n'est pas installe ou n'est pas reconnu.
        echo Assurez-vous d'avoir coche "Add Python to PATH" lors de l'installation.
        pause
        exit /b
    )
    echo Environnement cree avec succes !
)

echo.
echo Activation de l'environnement...
call .venv\Scripts\activate
echo Environnement active ! 

echo.
echo Installation des librairies...
REM Verifie et installe base.txt dans le dossier requirements
if exist requirements\base.txt (
    echo [Installation] Lecture de requirements\base.txt...
    pip install -r requirements\base.txt
) else (
    echo [Info] Aucun fichier base.txt trouve dans le sous-dossier "requirements".
)

REM Verifie et installe dev.txt dans le dossier requirements
if exist requirements\dev.txt (
    echo [Installation] Lecture de requirements\dev.txt...
    pip install -r requirements\dev.txt
) else (
    echo [Info] Aucun fichier dev.txt trouve dans le sous-dossier "requirements".
)

echo.
echo ==========================================
echo Termine ! Pour desactiver, tapez "deactivate"
echo ==========================================
echo.

REM Garde la fenetre ouverte dans l'environnement virtuel
cmd /k