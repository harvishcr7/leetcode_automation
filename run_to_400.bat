@echo off
cd /d "%~dp0"
if exist "C:\Users\balas\anaconda3\python.exe" (
    set "PY=C:\Users\balas\anaconda3\python.exe"
) else (
    set "PY=python"
)

echo Starting Fast Batch Solver to 400 problems...
"%PY%" batch_solver.py 400
pause

