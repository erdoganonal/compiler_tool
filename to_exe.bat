rmdir build /s /q
rmdir dist /s /q
del build_out.txt
del compiler_tool.spec

pyinstaller.exe  -w -F compiler_tool.py
REM pyinstaller.exe --onefile compiler_tool.py

rmdir build /s /q
del build_out.txt
del compiler_tool.spec