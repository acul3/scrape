import sys
from pathlib import Path
import re
import fasttext
import pandas as pd

end_of_text = "<|endoftext|>"
minimal_votes = 10
story_list_path = "wattpad_stories_indonesia_all.csv"
stories = []
if len(sys.argv) != 3:
    print(sys.argv[0], "<source dir> <destination dir>")
    exit(1)
source_dir = Path(sys.argv[1])
dest_dir = Path(sys.argv[2])
ft_model = fasttext.load_model('lid.176.ftz')

story_votes = {}
df = pd.read_csv(story_list_path)
for i, row in df.iterrows():
    story_votes[row["id"]] = row["voteCount"]

def language_check(path):
    with open(path, "r") as file:
        count = 0
        for _ in file:
            if count >= 20:
                break
            count += 1
        char_count = 0
        for line in file:
            char_count += len(line)
            if char_count > 100:
                break
        sentence = ""
        for line in file:
            sentence += line
            if len(sentence) > 1000:
                lang_predictions, lang_probability = ft_model.predict(sentence.replace("\n", " "), k=3)
                return lang_predictions, lang_probability
        return None

dest_dir.mkdir(parents=True, exist_ok=True)
for path in sorted(source_dir.glob("**/*.txt")):
    if path.stat().st_size < 3000:
        continue
    lang = language_check(path)
    if lang is None or lang[0][0] != '__label__id':
        continue
    if lang[0][1] == '__label__ms' and lang[1][1] >= 0.3:
        continue
    try:
        story_id = re.match(r".+_(\d+).txt", path.name)
        story_id = int(story_id.group(1))
    except:
        print(f"Can't find id of {path.name}")
        continue
    if story_id not in story_votes:
        continue
    print(f"{path.name} {story_votes[story_id]}")
    if story_votes[story_id] < minimal_votes:
        continue
    file_counter = 0
    story = {}
    with open(path, "r") as file:
        file_out = open(dest_dir / f"{path.stem}_{file_counter:03d}.txt", "w")
        file_out.write(f"{end_of_text}\n")
        for line in file:
            line = line.strip()
            if line == "":
                continue
            line = re.sub(r'Wattpad', "Buku cerita", line)
            line = re.sub(r'Wattpad', "buku cerita", line, flags=re.IGNORECASE)
            key_value = re.split('\s+', line, 1)
            if len(key_value) == 2:
                story["title"] = key_value[1]
                file_out.write(f"Title: {story['title']}\n")
            break
        for line in file:
            line = re.sub(r'Wattpad', "Buku cerita", line)
            line = re.sub(r'Wattpad', "buku cerita", line, flags=re.IGNORECASE)
            if not line.startswith("by "):
                continue
            line = line.strip()
            key_value = re.split('\s+', line, 1)
            if len(key_value) != 2:
                continue
            else:
                story["author"] = key_value[1]
            break
        for line in file:
            line = line.strip()
            if line == "":
                continue
            key_value = re.split(': +', line, 1)
            if len(key_value) != 2:
                continue
            else:
                if key_value[0] == "Category":
                    story["category"] = key_value[1]
                    file_out.write(f"Category: {story['category']}\n")
                elif key_value[0] == "Read Count":
                    break
        for line in file:
            if not line.startswith("     "):
                continue
            line = re.sub(r'Wattpad', "Buku cerita", line)
            line = re.sub(r'Wattpad', "buku cerita", line, flags=re.IGNORECASE)
            line = line.strip()
            file_out.write(f"{line}")
            break
        last_line = None

        for line in file:
            line = re.sub(r'Wattpad', "Buku cerita", line)
            line = re.sub(r'Wattpad', "buku cerita", line, flags=re.IGNORECASE)
            if line.startswith("     "):
                file_out.write(f"{end_of_text}\n")
                file_out.close()
                file_counter += 1
                file_out = open(dest_dir / f"{path.stem}_{file_counter:03d}.txt", "w")
                file_out.write(f"{end_of_text}\n")
                if "title" in story:
                    file_out.write(f"Title: {story['title']}\n")
                if "category" in story:
                    file_out.write(f"Category: {story['category']}\n")
                file_out.write(f"{line.strip()}\n")
                continue
            line = line.strip()
            line = re.sub(r'\*\*([^*]{,10})\*\* ?', r"\1", line)
            line = re.sub(r'(\*\*[^*]+\*\*|_)', '', line)
            if re.match(r'(.*?)\*\*[^*]+', line):
                star_end = False
                for line in file:
                    if re.match(r'.*\*\*', line):
                        star_end = True
                        break
                last_line = ""
                if star_end:
                    continue
            line = re.sub(r'\([^)]+\)\[[^]]+]', "", line)
            line = re.sub(r'https?://[^ )\]]+', "", line)
            if (line == "" and last_line == "") or line == "End file.":
                last_line = line
                continue
            if line == "":
                file_out.write(f"\n")
                last_line = line
                continue
            line = re.sub(r'(-­)', '-', line)
            if len(line) < 40:
                if last_line == "":
                    file_out.write(f"\n{line}")
                else:
                    file_out.write(f" {line}")
            else:
                file_out.write(f"\n{line}")
            last_line = line
        file_out.write(f"{end_of_text}\n")
    file_out.close()