from pathlib import Path
import re
import argparse
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src_dir", type=str, required=True,
                        help="Source directory where the books are stored")
    parser.add_argument("--dst_dir", type=str, required=True,
                        help="Destionation directory where the books in text format will be stored")
    parser.add_argument("--book_list", type=str, required=False, default="book_list",
                        help="The name of book list")
    parser.add_argument("--single_newline", action='store_true', default=False,
                        help="Print/write text as raw")
    args = parser.parse_args()

    book_dir = Path(args.src_dir)
    dest_dir = Path(args.dst_dir)
    single_newline = args.single_newline

    for subdir_1 in Path(book_dir).iterdir():
        if subdir_1.is_dir() and len(subdir_1.name) == 1:
            for subdir_2 in Path(subdir_1).iterdir():
                out_dir = dest_dir/subdir_1.name/subdir_2.name
                out_dir.mkdir(parents=True, exist_ok=True)
                if (subdir_2/"book.json").stat().st_size == 0:
                    continue
                with open(subdir_2/"book.json", "r") as book_file:
                    book = json.load(book_file)
                    try:
                        with open(out_dir/"book.txt", "w") as file_txt:
                            file_txt.write("<|endoftext|>\n")
                            file_txt.write(f"Title: {book['book_detail']['book_title']}\n")
                            file_txt.write(f"Category: {book['category']}\n")
                            if single_newline:
                                description = re.sub(r'\n+', '\n', f"{book['book_detail']['book_description'].strip()}\n")
                            else:
                                description = book['book_detail']['book_description'].strip()
                            file_txt.write(f"Description: {description}")
                            file_txt.write("<|endoftext|>")
                    except KeyError:
                        continue
                for file in sorted(subdir_2.glob("chapter_*.json")):
                    if file.stat().st_size == 0:
                        continue
                    with open(file, "r") as chapter_file:
                        chapter = json.load(chapter_file)
                        try:
                            with open(out_dir/(file.stem+".txt"), "w") as file_txt:
                                file_txt.write("<|endoftext|>\n")
                                file_txt.write(f"Title: {book['book_detail']['book_title']}\n")
                                file_txt.write(f"Category: {book['category']}\n")
                                file_txt.write(f"{chapter['chapter_name']}\n")
                                if single_newline:
                                    chapter_content = re.sub(r'\n+', '\n', f"{chapter['chapter_content'].strip()}\n")
                                else:
                                    chapter_content = chapter['chapter_content'].strip()
                                file_txt.write(f"{chapter_content}")
                                file_txt.write("<|endoftext|>")
                        except KeyError:
                            continue


if __name__ == '__main__':
    main()
