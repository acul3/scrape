import sys
from pathlib import Path
import re
import fasttext


stories = []
if len(sys.argv) != 2:
    print(sys.argv[0], "<dir>")
    exit(1)
story_dir = Path(sys.argv[1])
ft_model = fasttext.load_model('lid.176.ftz')


def language_check(path):
    #print("path:", path)
    with open(path, "r") as file:
        story = {}
        for line in file:
            line = line.strip()
            if line == "":
                continue
            key_value = re.split('\s+', line, 1)
            if len(key_value) == 2:
                story["title"] = key_value[1]
            break
        for line in file:
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
                elif key_value[0] == "Read Count":
                    break
        for line in file:
            if not line.startswith("     "):
                continue
            line = line.strip()
            break

        sentence = ""
        for line in file:
            sentence += line
            if len(sentence) > 300:
                lang_predictions, lang_probability = ft_model.predict(sentence.replace("\n", " "), k=3)
                return lang_predictions, lang_probability, sentence
        return None


for path in sorted(story_dir.glob("**/*.txt")):
    if path.stat().st_size < 2000:
        continue
    lang = language_check(path)
    if lang is None:
        print(f"path is too small")
    elif lang[0][0] != '__label__id':
        print(f"path: {path}: {lang[0][0]}")
        print(lang[2])