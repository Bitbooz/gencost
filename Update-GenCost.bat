@echo off
cd /d C:\Users\frode\Desktop\gencost
echo Starting update...
python regenerate_html.py
echo.
echo Adding and pushing changes...
git add index.html voice.html music.html
git commit -m "Daily price update %date% %time%"
git push
echo.
echo Done. Press any key to close.
pause