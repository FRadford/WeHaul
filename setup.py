import cx_Freeze
import os
import sys

os.environ['TCL_LIBRARY'] = r'C:\Program Files\Python36\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Program Files\Python36\tcl\tk8.6'

base = None
extension = ""
if sys.platform == "win32":
    base = "Win32GUI"
    extension = ".exe"
    
exe_name = "We Haul"

cx_Freeze.setup(
    name=exe_name,
    options={"build_exe": {"packages": ["pygame", "extend", "backend.systems"],
                           "includes": ["pygame"],
                           "include_files": ["assets/"]}},
    executables=[cx_Freeze.Executable("main.py", base=base, targetName=exe_name + extension)]
)
