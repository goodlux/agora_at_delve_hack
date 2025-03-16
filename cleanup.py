#!/usr/bin/env python3
import os
import shutil

# Files to remove
typescript_files = [
    "/Users/rob/repos/agora_at_delve_hack/src/adapters/agora-adapter.ts",
    "/Users/rob/repos/agora_at_delve_hack/src/adapters/atproto-adapter.ts",
    "/Users/rob/repos/agora_at_delve_hack/src/index.ts",
    "/Users/rob/repos/agora_at_delve_hack/src/types.ts",
    "/Users/rob/repos/agora_at_delve_hack/package.json",
    "/Users/rob/repos/agora_at_delve_hack/tsconfig.json"
]

# Remove each file
for file_path in typescript_files:
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Removed: {file_path}")
    else:
        print(f"File not found: {file_path}")

# Remove src directory entirely since it only contains TS files
src_dir = "/Users/rob/repos/agora_at_delve_hack/src"
if os.path.exists(src_dir) and os.path.isdir(src_dir):
    shutil.rmtree(src_dir)
    print(f"Removed directory: {src_dir}")

print("Cleanup completed!")
