@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if errorlevel 1 exit /b 1

echo MODE JARINGAN LOKAL EKA
 echo Perhatian: Mode jaringan membuat aplikasi dapat diakses perangkat lain pada Wi-Fi yang sama.
echo Pastikan jaringan terpercaya dan tidak ada port forwarding ke internet.
echo Pemasangan PWA di HP memerlukan HTTPS yang sah, bukan akses HTTP melalui alamat IP.
echo.
set /p "ANSWER=Lanjut untuk uji coba jaringan lokal? (YA/TIDAK): "
if /I not "%ANSWER%"=="YA" exit /b 0
set "EKA_HOST=0.0.0.0"
call "%~dp0JALANKAN_WINDOWS.bat"
endlocal
