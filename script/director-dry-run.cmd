@echo off
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0director-dry-run.ps1" %*
