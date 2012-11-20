@echo off
cd deps\c-ares
nmake /f Makefile.msvc
cd ..\..
python setup_msvc.py build bdist_msi
