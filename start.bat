@echo off
cd /d "%~dp0"

:: Créer .env si inexistant
if not exist .env (
    copy .env.example .env
)

:: Installer dépendances
echo ==^> Installation des dépendances...
pip install -r requirements.txt

:: Lancer le crawler
echo.
echo ==^> Lancement du crawler...
bash scripts/crawl.sh

echo.
echo ==^> Résultats dans .\site\
pause
