@echo off
cd /d "%~dp0"
if exist "C:\Users\balas\anaconda3\python.exe" (
    set "PY=C:\Users\balas\anaconda3\python.exe"
) else (
    set "PY=python"
)

echo Running LeetCode Daily Agent...
"%PY%" leetcode_agent.py
pause

