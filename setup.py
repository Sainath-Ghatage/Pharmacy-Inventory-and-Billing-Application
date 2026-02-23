import sys
from cx_Freeze import setup, Executable

# 1. Dependencies and exclusions
build_exe_options = {
    "packages": ["os", "sys", "sqlite3", "datetime", "smtplib", "PyQt6", "pandas", "matplotlib", "reportlab", "numpy", "pyautogui"],
    "excludes": ["tkinter", "unittest", "tensorflow", "torch", "scipy"], 
    "include_files": ["pharmacy.ico"] 
}

# 2. Hide the console window
base = None
if sys.platform == "win32":
    base = "gui"

# 3. Executable configuration
executables = [
    Executable(
        script="main.py",
        base=base,
        target_name="PharmacyApp.exe",
        icon="pharmacy.ico"
    )
]

# 4. Run setup
setup(
    name="PharmacyApp",
    version="1.0",
    description="Pharmacy Management System",
    options={"build_exe": build_exe_options},
    executables=executables
)