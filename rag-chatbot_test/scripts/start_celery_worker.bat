@echo off
REM Celery Worker 실행 스크립트 (Windows)
REM 사용법: scripts\start_celery_worker.bat

REM 현재 스크립트의 디렉토리로 이동
cd /d %~dp0..

REM Windows에서는 solo 풀 사용 (prefork 미지원)
echo Celery Worker를 시작합니다 (Windows - solo pool)...
echo 프로젝트 디렉토리: %CD%
echo.
celery -A app.celery_app worker --loglevel=info --pool=solo

pause

