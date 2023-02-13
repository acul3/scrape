from pathlib import Path
import re
import argparse
import json
from datasets import DatasetDict, Dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src_dir", type=str, required=True,
                        help="Source directory where the books are stored")
    parser.add_argument("--dataset", type=str, required=True,
                        help="Dataset name where the books in dataset format will be stored")
    parser.add_argument("--book_list", type=str, required=False, default="book_list",
                        help="The name of book list")
    parser.add_argument("--single_newline", action='store_true', default=False,
                        help="Print/write text as raw")
    parser.add_argument("--save_to_directory", action='store_true', default=True,
                        help="Save the dataset to a directory")
    parser.add_argument("--save_to_hub", action='store_true', default=False,
                        help="Save the dataset to HuggingFace Hub")
    args = parser.parse_args()

    book_dir = Path(args.src_dir)
    dataset_name = args.dataset
    single_newline = args.single_newline
    books = []
    id = -1
    for subdir_1 in Path(book_dir).iterdir():
        if subdir_1.is_dir() and len(subdir_1.name) == 1:
            for subdir_2 in Path(subdir_1).iterdir():
                if (subdir_2/"book.json").stat().st_size == 0:
                    continue
                id += 1
                current_book = { "id": id, "text": "" }
                with open(subdir_2/"book.json", "r") as book_file:
                    book = json.load(book_file)
                    try:
                        current_book["text"] += f"Title: {book['book_detail']['book_title']}\n"
                        current_book["text"] += f"Category: {book['category']}\n"
                        if single_newline:
                            description = re.sub(r'\n+', '\n', f"{book['book_detail']['book_description'].strip()}")
                        else:
                            description = book['book_detail']['book_description'].strip()
                        current_book["text"] += f"Text:\n"
                    except KeyError:
                        continue
                for file in sorted(subdir_2.glob("chapter_*.json")):
                    if file.stat().st_size == 0:
                        continue
                    with open(file, "r") as chapter_file:
                        chapter = json.load(chapter_file)
                        try:
                            current_book["text"] += f"{chapter['chapter_name']}\n"
                            if single_newline:
                                content = re.sub(r'\n+', '\n', f"{chapter['chapter_content'].strip()}\n")
                            else:
                                content = chapter['chapter_content'].strip()
                            current_book["text"] += f"{content}\n"
                        except KeyError:
                            continue
                current_book["text"] += f"Description: {description}\n"
                current_book["text"] += f"<|endoftext|>\n"
                books.append(current_book)
                if id % 100 == 0 and id > 0:
                    print(f"\n", end="", flush=True)
                print(".", end="", flush=True)
    dataset = DatasetDict()
    dataset["train"] = Dataset.from_list(books)
    if args.save_to_directory:
        dataset.save_to_disk(dataset_name)
    if args.save_to_hub:
        dataset.push_to_hub(dataset_name, private=True)
    print(f"\nSaved {id+1} books to dataset {dataset_name}")


if __name__ == '__main__':
    main()
