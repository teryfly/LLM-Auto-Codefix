# operations/file/directory_ops.py

import os

def list_files_recursively(root_dir: str, ignore_hidden: bool = True) -> list:
    file_list = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if ignore_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            filenames = [f for f in filenames if not f.startswith('.')]
        for filename in filenames:
            file_list.append(os.path.join(dirpath, filename))
    return file_list

def create_directory(path: str):
    os.makedirs(path, exist_ok=True)

def remove_empty_dirs(root_dir: str):
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        if not dirnames and not filenames:
            os.rmdir(dirpath)