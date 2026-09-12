'''
(open the root folder
check if there is any subfolder, if exists - open that folder
in that folder check again if there is a folder) do this till only files no folder


{first - get rid of duplicate files -> same name or name ends with - copy, if the name is same check the file size the file with bigger file size stays.

second - sort the files in ascending order of creation

third - group the files with same creation date in same folder} repeat till no file left, all folders

now check if the current folder is the root folder or not, if not the root folder, 
cut all the files in the current folder and move them into next subfolder of root, 
if no subfolder then exit the program

print done
'''
import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
 
 
def _file_hash(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    """
    Full content hash (SHA-256), read in chunks so large media files
    don't need to be loaded into memory at once.
 
    This is the safety-critical piece: two files are only ever treated
    as duplicates if their bytes are identical, never just because their
    names look similar.
    """
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()
 
 
def organize_media_safely(root_dir):
    root_path = Path(root_dir).resolve()
    if not root_path.exists():
        print("Root directory does not exist.")
        return
 
    dupe_folder = root_path / "_duplicates_to_review"
    print("Starting safe organization...")
 
    # Traverse from deepest subfolders up to the root
    for current_dir, subdirs, files in os.walk(root_path, topdown=False):
        current_path = Path(current_dir)
 
        # Skip the root directory and our review folder during traversal
        if current_path == root_path or current_path == dupe_folder:
            continue
 
        # 1. Group files in this folder by "cleaned" name (candidate duplicates)
        file_dict = {}
        for file in current_path.iterdir():
            if file.is_file():
                # Clean up the name to map copies to their original (e.g., "img - copy.jpg" -> "img.jpg")
                name_lower = file.stem.lower()
                for suffix in [" - copy", " (2)", " (3)", " (4)"]:
                    if name_lower.endswith(suffix):
                        name_lower = name_lower[: -len(suffix)]
                        break
 
                key = f"{name_lower}{file.suffix.lower()}"
 
                if key not in file_dict:
                    file_dict[key] = [file]
                else:
                    file_dict[key].append(file)
 
        # Process candidate duplicates found within this folder.
        # A matching cleaned name is only a CANDIDATE - it is not proof
        # the files are actually copies of each other. We only ever move
        # a file into the review folder if another file in the same
        # candidate group has byte-identical content.
        for key, candidates in file_dict.items():
            if len(candidates) <= 1:
                continue
 
            # Bucket candidates by actual content hash. Only files that
            # land in the same bucket are true duplicates.
            hash_buckets = {}
            for f in candidates:
                try:
                    h = _file_hash(f)
                except OSError as e:
                    print(f"  Warning: could not hash {f}, leaving it alone ({e})")
                    h = None  # treat as its own unique bucket below
                hash_buckets.setdefault(h, []).append(f)
 
            kept = []
            for h, group in hash_buckets.items():
                if h is not None and len(group) > 1:
                    # These are genuinely identical files - safe to dedupe.
                    group.sort(key=lambda f: f.stat().st_size, reverse=True)
                    keeper = group[0]
                    kept.append(keeper)
 
                    dupe_folder.mkdir(exist_ok=True)
                    for dup in group[1:]:
                        safe_dupe_path = dupe_folder / dup.name
                        counter = 1
                        while safe_dupe_path.exists():
                            safe_dupe_path = dupe_folder / f"{dup.stem}_{counter}{dup.suffix}"
                            counter += 1
                        shutil.move(str(dup), str(safe_dupe_path))
                else:
                    # Same-ish name, different content (or unhashable) -
                    # these are NOT duplicates. Leave every file in the
                    # group alone; they'll just get collision-safe names
                    # if they clash later when moved.
                    kept.extend(group)
 
            file_dict[key] = kept
 
        # 2. Sort remaining files by "date modified"
        remaining_files = [f for files_list in file_dict.values() for f in files_list]
        remaining_files.sort(key=lambda f: f.stat().st_mtime)
 
        # 3. Group files by modification date (including year) and move to root directory
        for file in remaining_files:
            mtime = file.stat().st_mtime
            date_folder_name = datetime.fromtimestamp(mtime).strftime("%d %B %Y").lower()
 
            target_folder = root_path / date_folder_name
            target_folder.mkdir(exist_ok=True)
 
            target_file = target_folder / file.name
 
            # If the file is already sitting in the correct destination
            # (e.g. this script is being re-run on an already-organized
            # folder), leave it exactly where it is instead of renaming
            # it with a spurious "_1" suffix.
            if target_file.resolve() == file.resolve():
                continue
 
            # Prevent filename collisions between different folders
            counter = 1
            while target_file.exists():
                target_file = target_folder / f"{file.stem}_{counter}{file.suffix}"
                counter += 1
 
            shutil.move(str(file), str(target_file))
 
        # Remove old empty subfolders
        try:
            current_path.rmdir()
        except OSError:
            pass
 
    print("Done! All media organized into date folders. Check '_duplicates_to_review' for any confirmed duplicates.")
 
 
# Example usage:
# organize_media_safely("/path/to/your/90gb_root_folder")
organize_media_safely("D:\\Akshat\\Downloads\\Coding\\PYTHON\\sorting_project\\sample/")