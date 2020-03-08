echo OFF
set icon_path=%cd%\compiler.ico

cls
IF "%1%" == "--with-console" (
    pyinstaller.exe --clean --onefile --icon "%icon_path%" --add-data "%icon_path%";"." compiler_tool.py
) ELSE (
    pyinstaller.exe --clean --noconsole --onefile --icon "%icon_path%" --add-data "%icon_path%";"." compiler_tool.py
)

rmdir build /s /q > nul 2>&1
del build_out.txt > nul 2>&1
del compiler_tool.spec > nul 2>&1