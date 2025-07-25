# operations/source/source_processor.py

from typing import List
import os

def filter_source_files(file_list: List[str], extensions: List[str]) -> List[str]:
    """
    Filters files by allowed extensions.
    """
    return [f for f in file_list if os.path.splitext(f)[1] in extensions]

def read_file_content(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def concatenate_files(file_list: List[str]) -> str:
    """
    Concatenate the content of all files in file_list into a single string.
    """
    contents = []
    for file_path in file_list:
        contents.append(read_file_content(file_path))
    return "\n".join(contents)