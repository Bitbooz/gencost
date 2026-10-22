@echo off
cd /d "%~dp0"
echo Starting price update...
python auto_update.py
git add *-pricing.json
git commit -m "Auto-update prices %date% %time%"
git push
echo Done. Site will update automatically on Netlify.
pause
