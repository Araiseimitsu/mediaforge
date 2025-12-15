@echo off
setlocal
chcp 65001 > nul

echo ==========================================
echo MediaForge Cloud Run Deploy Script
echo ==========================================

echo.
echo checking gcloud configuration...
call gcloud config get-value project > temp_project_id.txt
set /p PROJECT_ID=<temp_project_id.txt
del temp_project_id.txt

if "%PROJECT_ID%"=="" (
    echo [ERROR] Google Cloud Project is not selected.
    echo Please run `gcloud config set project [PROJECT_ID]` or `gcloud init`.
    pause
    exit /b 1
)

echo.
echo Target Project: %PROJECT_ID%
echo Target Region: asia-northeast1 (Tokyo)
echo Service Name: mediaforge
echo.
set /p CONFIRM="Are you sure you want to deploy? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Deployment cancelled.
    exit /b 0
)

echo.
echo Starting deployment... this may take a few minutes.
echo.

call gcloud run deploy mediaforge ^
  --source . ^
  --region asia-northeast1 ^
  --allow-unauthenticated

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Deployment failed.
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Deployment completed successfully!
pause
