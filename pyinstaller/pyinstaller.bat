python -O C:\pyinstaller\Configure.py
python -O C:\pyinstaller\Makespec.py --onefile --upx --icon=furion.ico ..\furion.py
python -O C:\pyinstaller\Build.py furion.spec

