
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_empty_files.py <file1> <file2> ...")
        sys.exit(0) # No files to check, exit gracefully

    files_to_check = sys.argv[1:]
    empty_files = []

    for file_path in files_to_check:
        if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
            empty_files.append(file_path)

    if empty_files:
        for file_path in empty_files:
            # Use GitHub Actions' error format
            print(f"::error file={file_path}::This file is empty and must have content.")
        sys.exit(1) # Exit with a non-zero status to fail the workflow

    print("All checked files have content.")
    sys.exit(0)

if __name__ == "__main__":
    main()
