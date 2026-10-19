from pathlib import Path
import string


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def clean_words(text: str) -> list:
    """Return lowercase words with punctuation removed; never empty strings."""
    lowered = text.lower()
    table = str.maketrans("", "", string.punctuation)
    cleaned = lowered.translate(table)
    return [word for word in cleaned.split() if word]


def count_words(words: list) -> int:
    return len(words)


def count_unique(words: list) -> int:
    return len(set(words))


def word_frequencies(words: list) -> dict:
    freqs = {}
    for word in words:
        freqs[word] = freqs.get(word, 0) + 1
    return freqs


def top_n(freqs: dict, n: int = 10) -> list:
    """Most common words first; ties broken alphabetically."""
    sorted_items = sorted(freqs.items(), key=lambda item: (-item[1], item[0]))
    return sorted_items[:n]


def average_word_length(words: list) -> float:
    if not words:
        return 0.0
    return sum(len(word) for word in words) / len(words)


def longest_words(words: list, n: int = 5) -> list:
    """n longest distinct words; longest first, ties alphabetical."""
    distinct = set(words)
    return sorted(distinct, key=lambda word: (-len(word), word))[:n]


def main() -> None:
    while True:
        filename = input("File to analyze: ").strip()
        path = Path(filename)
        try:
            text = load_text(path)
            break
        except FileNotFoundError:
            print(f"File not found: {filename}. Try again.")

    words = clean_words(text)
    freqs = word_frequencies(words)
    top_words = top_n(freqs)
    longest = longest_words(words)

    print()
    print(f"Total words:      {count_words(words):,}")
    print(f"Unique words:     {count_unique(words):,}")
    print(f"Avg word length:  {average_word_length(words):.2f}")
    print(f"Longest words:    {', '.join(longest)}")
    print()
    print(f"Top {len(top_words)} words:")
    for word, count in top_words:
        print(f"  {word:<15} {count}")


if __name__ == "__main__":
    main()
