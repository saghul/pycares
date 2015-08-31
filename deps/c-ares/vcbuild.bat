@echo off

cd %~dp0

if /i "%1"=="help" goto help
if /i "%1"=="--help" goto help
if /i "%1"=="-help" goto help
if /i "%1"=="/help" goto help
if /i "%1"=="?" goto help
if /i "%1"=="-?" goto help
if /i "%1"=="--?" goto help
if /i "%1"=="/?" goto help

@rem Process arguments.
set target=Build

:next-arg
if "%1"=="" goto args-done
if /i "%1"=="clean"        set target=Clean&goto arg-ok
:arg-ok
shift
goto next-arg
:args-done

if defined WindowsSDKDir goto select-target
if defined VCINSTALLDIR goto select-target

@rem Look for Visual Studio 2008
if not defined VS90COMNTOOLS goto vc-set-notfound
if not exist "%VS90COMNTOOLS%\..\..\vc\vcvarsall.bat" goto vc-set-notfound
call "%VS90COMNTOOLS%\..\..\vc\vcvarsall.bat" %vs_toolset%
goto select-target

:vc-set-notfound
echo Warning: Visual Studio not found

:select-target
if "%target%"=="Build" goto compile
if "%target%"=="Clean" goto clean

:compile
nmake /f Makefile.msvc
goto exit

:clean
nmake /f Makefile.msvc clean
goto exit

:help
echo vcbuild.bat [clean]
echo Examples:
echo   vcbuild.bat              : builds c-ares
echo   vcbuild.bat clean        : cleans the build
goto exit

:exit
