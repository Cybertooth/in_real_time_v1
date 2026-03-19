@echo off
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0director-fresh-start.ps1" %*
