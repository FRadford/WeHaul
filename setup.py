import cx_Freeze
import os

os.environ['TCL_LIBRARY'] = r'C:\Program Files\Python36\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Program Files\Python36\tcl\tk8.6'

cx_Freeze.setup(
    name="We Haul",
    options={"build_exe": {"packages": ["pygame", "extend", "backend.systems"],
                           "includes": ["pygame"],
                           "include_files": ["assets/"]}},
    executables=[cx_Freeze.Executable("main.py", targetName="we_haul.exe")]
)
