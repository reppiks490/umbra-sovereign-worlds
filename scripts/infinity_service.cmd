@echo off
setlocal
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set TOKENIZERS_PARALLELISM=false
set PYTHONNOUSERSITE=1
"%USERPROFILE%\projects\umbra-polymind-runtime\Scripts\python.exe" "%~dp0infinity_service.py" --root "%USERPROFILE%\projects\umbra-agentic-native-20261124"
exit /b %errorlevel%
