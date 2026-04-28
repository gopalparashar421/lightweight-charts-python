@echo off
setlocal

set "ERROR=[ERROR] "
set "INFO=[INFO] "
set "WARNING=[WARNING] "

rd /s /q dist\bundle.js dist\typings\ 2>nul
del /f /q dist\bundle.js 2>nul
if %errorlevel% equ 0 (
    echo %INFO%deleted bundle.js and typings..
) else (
    echo %WARNING%could not delete old dist files, continuing..
)

call npx rollup -c rollup.config.js
if %errorlevel% neq 0 exit /b 1

copy /y dist\bundle.js lightweight_charts\js\ >nul
copy /y src\general\styles.css lightweight_charts\js\ >nul
if %errorlevel% equ 0 (
    echo %INFO%copied bundle.js, style.css into python package
) else (
    echo %ERROR%could not copy dist into python package ?
    exit /b 1
)

copy /y node_modules\lightweight-charts\dist\lightweight-charts.standalone.development.js lightweight_charts\js\ >nul
if %errorlevel% equ 0 (
    echo %INFO%copied lightweight-charts standalone file into python package
) else (
    echo %ERROR%could not copy lightweight-charts standalone file ?
    exit /b 1
)

echo.
echo [BUILD SUCCESS]