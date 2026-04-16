@echo off
echo =========================================
echo   JiuZhang (九章) PyPI Upload Script
echo =========================================

REM Step 1: Bump patch version
echo.
echo Step 1: Bumping patch version...
for /f "tokens=2 delims==" %%a in ('findstr "__version__" jiuzhang\__init__.py') do set CURRENT_VERSION=%%~a
for /f "tokens=1,2,3 delims=." %%a in ("%CURRENT_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
    set PATCH=%%c
)
set /a NEW_PATCH=%PATCH% + 1
set NEW_VERSION=%MAJOR%.%MINOR%.%NEW_PATCH%

powershell -Command "(gc jiuzhang\__init__.py) -replace '__version__ = \"%CURRENT_VERSION%\"', '__version__ = \"%NEW_VERSION%\"' | Out-File -encoding ASCII jiuzhang\__init__.py"
echo Version bumped: %CURRENT_VERSION% -^> %NEW_VERSION%

REM Step 2: Clean old builds
echo.
echo Step 2: Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.egg-info rmdir /s /q *.egg-info
if exist jiuzhang.egg-info rmdir /s /q jiuzhang.egg-info

REM Step 3: Install build tools
echo.
echo Step 3: Installing build tools...
pip install --upgrade build twine
if %errorlevel% neq 0 (
    echo Failed to install build tools!
    exit /b 1
)

REM Step 4: Build package
echo.
echo Step 4: Building package...
python -m build
if %errorlevel% neq 0 (
    echo Build failed!
    exit /b 1
)
echo Running twine check...
twine check dist\*

REM Step 5: Upload to PyPI
echo.
echo Step 5: Uploading to PyPI...
twine upload dist\*
if %errorlevel% neq 0 (
    echo Upload failed!
    exit /b 1
)

echo.
echo =========================================
echo   Upload complete! Version: %NEW_VERSION%
echo =========================================
pause
