@echo off
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0director-tests.ps1" %*
