from pathlib import Path
import string


BASE_DIR = Path(__file__).resolve().parent
file_path = BASE_DIR / "sample.txt"

def load_text(path:str)->str:
    with open(path, "r") as file:
        content = file.read()
        return content

def clean_words(text:str)->str:
    lowercase_string = text.lower()
    table = str.maketrans('', '', string.punctuation)
    cleaned_text = lowercase_string.translate(table)
    return cleaned_text

def count_words(words: str)->int:
    return len(words.split(" "))

def count_unique(words: str)->set:
    words_array = words.split(" ")
    unique_words = set(words_array)
    return len(unique_words)

file_content = load_text(file_path)
cleaned_words = clean_words(file_content)
word_count = count_words(cleaned_words)
unique_words = count_unique(cleaned_words)

print(f'file content: {file_content}')
print(f"cleaned words: {cleaned_words}")
print(f"word count: {word_count}")
print(f"unique words:{unique_words}")