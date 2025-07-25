# operations/file/file_manager.py

import shutil
import os

class FileManager:
    @staticmethod
    def copy_directory(src: str, dst: str, overwrite: bool = True):
        if os.path.exists(dst):
            if overwrite:
                shutil.rmtree(dst)
            else:
                raise FileExistsError(f"Destination directory {dst} already exists")
        shutil.copytree(src, dst)

    @staticmethod
    def delete_directory(path: str):
        if os.path.exists(path) and os.path.isdir(path):
            shutil.rmtree(path)

    @staticmethod
    def sync_files(src_dir: str, dst_dir: str, exclude: list = None):
        """
        Copy files from src_dir to dst_dir, optionally excluding certain files/directories.
        """
        exclude = set(exclude or [])
        for root, dirs, files in os.walk(src_dir):
            rel_root = os.path.relpath(root, src_dir)
            dst_root = os.path.join(dst_dir, rel_root)
            os.makedirs(dst_root, exist_ok=True)
            for file in files:
                if file in exclude:
                    continue
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_root, file)
                shutil.copy2(src_file, dst_file)

    @staticmethod
    def remove_file(path: str):
        if os.path.isfile(path):
            os.remove(path)

    @staticmethod
    def file_exists(path: str) -> bool:
        return os.path.isfile(path)

    @staticmethod
    def dir_exists(path: str) -> bool:
        return os.path.isdir(path)