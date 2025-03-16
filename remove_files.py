#!/usr/bin/env python3
import os
import shutil

# List files to remove
files_to_remove = [
    "/Users/rob/repos/agora_at_delve_hack/package.json",
    "/Users/rob/repos/agora_at_delve_hack/tsconfig.json"
]

# Remove each file
for file_path in files_to_remove:
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed: {file_path}")
        else:
            print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error removing {file_path}: {e}")

# Remove src directory since it contains TypeScript files
src_dir = "/Users/rob/repos/agora_at_delve_hack/src"
try:
    if os.path.exists(src_dir):
        shutil.rmtree(src_dir)
        print(f"Removed directory: {src_dir}")
    else:
        print(f"Directory not found: {src_dir}")
except Exception as e:
    print(f"Error removing directory {src_dir}: {e}")

print("Cleanup completed!")
