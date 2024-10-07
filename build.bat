rmdir /S /Q build
pyinstaller --onefile --name "P21 Data Exporter" --icon=logo.ico --collect-submodules=p21api --collect-submodules=gui main.py