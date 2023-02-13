from pathlib import Path
import sys
from tqdm import tqdm
import json

def main():
    if len(sys.argv) != 2:
        exit(1)
    book_dir = Path(sys.argv[1])
    files_size = 0
    counter = 0
    for file in book_dir.glob("**/chapter*.json"):
        counter += 1
        # print(file.name)
        if file.stat().st_size == 0:
            continue
        try:
            chapter = json.load(open(file, "r"))
            files_size += len(chapter["chapter_content"])
            if counter%1000 == 0:
                print("*",  flush=True, end="")
        except:
            pass
    print(f"\nNumber of files: {counter}, Size: {files_size/(1024*1024):5.2f}MB")


if __name__ == '__main__':
    main()
