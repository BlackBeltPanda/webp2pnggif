# webp2pnggif
A simple Python script with UI to convert selected WebP files to PNG or GIF automatically.

## Features:
- Select one or more files from one or more locations. Supports drag-and-drop.
- Manage the selected files in the file list; remove files or add more. Supports multi-select and the delete keyboard key.
- Automatically determines if the WebP should be converted to PNG or GIF based on how many frames are in the image. 1 frame = PNG, 2+ frames = GIF.
- Output all converted files to a selected folder. Retains selected folder between conversions until UI is closed.

## Requirements:
- [Python](https://www.python.org/)
- [Pillow](https://pypi.org/project/pillow/): `pip install Pillow`
- [TkinterDnD2](https://pypi.org/project/tkinterdnd2/): `pip install tkinterdnd2`

## Standalone Packaging:
To package the script as an executable file bundled with its dependencies for use on systems without needing to install the above requirements, you can use [PyInstaller](https://pyinstaller.org/en/stable/):<br>
`pip install pyinstaller`

In the same folder that "WebPConverter.py" exists in, run:<br>
`pyinstaller --noconsole --onefile --collect-all tkinterdnd2 --name "WebPConverter" WebPConverter.py`

This will output a couple directories and a .spec file. Open the *"dist"* directory and you should find the **"WebPConverter.exe"** executable file, which you can now move to another location or PC.

### Troubleshooting Common Issues
#### "Failed to load tkdnd library" Error:
If you run the EXE and it immediately crashes or gives an error about tkdnd, it means PyInstaller couldn't find the drag-and-drop binaries automatically. If this happens, you need to manually tell PyInstaller where tkinterdnd2 is hiding:
1. Create a temporary python file (e.g., find_path.py) and run this code:
```Python
import tkinterdnd2
import os
print(os.path.dirname(tkinterdnd2.__file__))
```
2. Copy the path it prints out.
3. Run the build command again using --add-data:
```Bash
pyinstaller --noconsole --onefile --add-data "PASTE_PATH_HERE;tkinterdnd2" your_script_name.py
```
*(Make sure to keep the ;tkinterdnd2 at the end of the path inside the quotes).*

#### Antivirus Warnings:
Because PyInstaller creates unverified EXE files, Windows Defender or other antivirus software might flag it as a "Trojan" or "Malware" (False Positive). This is normal for unsigned Python scripts. You may need to add an exception for the file on the target machine.

## Why does this exist?
Many applications still don't support WebP images, especially animated ones. I originally wrote a basic WebP to GIF converter so I could send animated WebP images in Discord. My fiancée recently ran into the same troubles with the graphic art software she uses not supporting WebP images she had tried to import as references. Any programmer with a significant other knows the outcome of this dilemma: I sat down and created this more polished version of my original converter script to make it easy enough for her to use.
