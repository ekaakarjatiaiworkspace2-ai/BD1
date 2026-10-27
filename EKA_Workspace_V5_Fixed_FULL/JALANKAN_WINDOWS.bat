@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if errorlevel 1 goto :folder_error

title EKA Workspace V6 - PT Eka Akar Jati
set "PYTHON_CMD=python"
where py >nul 2>&1
if errorlevel 1 goto :check_python
py -3 --version >nul 2>&1
if errorlevel 1 goto :check_python
set "PYTHON_CMD=py -3"

:check_python
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 goto :no_python

echo.
echo ================================================
echo   EKA WORKSPACE V6 - PT EKA AKAR JATI
echo ================================================
echo [1/3] Memeriksa lingkungan Python...
if exist ".venv\Scripts\python.exe" goto :dependencies
%PYTHON_CMD% -m venv ".venv"
if errorlevel 1 goto :venv_failed

:dependencies
echo [2/3] Memeriksa kebutuhan aplikasi...
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, multipart, psycopg, boto3" >nul 2>&1
if not errorlevel 1 goto :run_app
echo Menginstal kebutuhan aplikasi. Internet diperlukan pada instalasi pertama.
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 goto :install_failed

:run_app
if not defined EKA_HOST set "EKA_HOST=127.0.0.1"
if not defined EKA_PORT set "EKA_PORT=8000"
echo.
echo [3/3] Memulai aplikasi...
echo Buka di browser: http://127.0.0.1:%EKA_PORT%
echo Bila menggunakan mode jaringan, gunakan alamat IP PC.
echo Tekan Ctrl+C untuk menghentikan server.
echo.
".venv\Scripts\python.exe" "app.py"
if errorlevel 1 goto :server_failed
goto :end

:folder_error
echo GAGAL: Tidak dapat membuka folder proyek.
goto :failed
:no_python
echo GAGAL: Python belum terpasang atau tidak ditemukan.
echo Pasang Python 3.11 atau versi lebih baru, lalu buka terminal baru.
goto :failed
:venv_failed
echo GAGAL: Tidak dapat membuat lingkungan Python .venv.
goto :failed
:install_failed
echo GAGAL: Instalasi dependensi gagal. Periksa internet dan pesan error di atas.
goto :failed
:server_failed
echo GAGAL: Server berhenti dengan error. Periksa pesan di atas.
goto :failed
:failed
pause
exit /b 1
:end
endlocal
