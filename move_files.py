import os
import shutil

# Create directories if they don't exist
directories = [
    'backend/src',
    'backend/models',
    'backend/utils',
    'backend/config',
    'backend/assets'
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)

# Define file movements
file_movements = {
    'backend/src': ['Body_Detection.py', 'app.py', 'ex.py'],
    'backend/models': ['yolov8n.pt'],
    'backend/config': ['haarcascade_frontalface_default.xml'],
    'backend/assets': ['captured_image.jpg', 'Ref_image.jpg', '0Ref_image.jpg']
}

# Move files
for target_dir, files in file_movements.items():
    for file in files:
        if os.path.exists(file):
            shutil.move(file, os.path.join(target_dir, file))
            print(f"Moved {file} to {target_dir}")
        else:
            print(f"File {file} not found")

# Keep requirements.txt and README.md in root directory
print("Done moving files!") 