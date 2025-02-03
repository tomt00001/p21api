# Generate version based on the current date (YYYY, M, D, 0)
$year = (Get-Date -Format yyyy)
$month = (Get-Date -Format MM) -as [int]  # Ensures no leading zero
$day = (Get-Date -Format dd) -as [int]    # Ensures no leading zero
$version = "$year,$month,$day,0"

# Create a version.txt file for PyInstaller
@"
# UTF-8 encoding required
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=($version),
        prodvers=($version),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904b0",
                    [
                        StringStruct("CompanyName", "Your Company"),
                        StringStruct("FileDescription", "P21 Data Exporter"),
                        StringStruct("FileVersion", "$version"),
                        StringStruct("InternalName", "P21 Data Exporter"),
                        StringStruct("OriginalFilename", "P21 Data Exporter.exe"),
                        StringStruct("ProductName", "P21 Data Exporter"),
                        StringStruct("ProductVersion", "$version")
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])])
    ]
)
"@ | Set-Content -Path "version.txt" -Encoding UTF8

# Run PyInstaller with the generated version
pyinstaller --onefile `
    --name "P21 Data Exporter" `
    --icon=logo.ico `
    --collect-submodules=p21api `
    --collect-submodules=gui `
    --version-file version.txt `
    main.py
