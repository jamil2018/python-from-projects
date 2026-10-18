# 03 · Text Analyzer

Read a text file and report statistics about it, like word count, most common words, and average word length.

**Builds on 02:** loops, input validation.

## Concepts
- Defining functions with `def`, parameters, return values, default arguments
- Docstrings
- String methods: `lower`, `split`, `strip`, `replace`, `isalpha`, `join`
- Lists: indexing, slicing, `append`, `len`, `sorted`
- Dictionaries: counting with `dict.get(key, 0) + 1`
- Reading files with `with open(...) as f:`
- `if __name__ == "__main__":`

## Setup
Create a `sample.txt` in this folder and paste a few paragraphs of any text into it. [Project Gutenberg](https://www.gutenberg.org/) has free books.

## Core requirements
Write these as **separate functions**. Each one takes its input as a parameter and returns a result. Only `main()` should call `print` or `input`.

| Function | Returns |
|----------|---------|
| `load_text(path)` | the file contents as a string |
| `clean_words(text)` | a list of lowercase words with punctuation removed |
| `count_words(words)` | total number of words |
| `count_unique(words)` | number of distinct words |
| `word_frequencies(words)` | a dict `{word: count}`, built by hand (no `Counter` yet) |
| `top_n(freqs, n=10)` | a list of `(word, count)` tuples, most common first |
| `average_word_length(words)` | a float |
| `longest_words(words, n=5)` | a list of the `n` longest distinct words |

`main()` asks for a filename and prints a report. If the file doesn't exist, catch `FileNotFoundError` and ask again.

## Example output
```
File to analyze: sample.txt

Total words:        1,284
Unique words:         512
Avg word length:     4.37
Longest words:      responsibility, extraordinary, ...

Top 10 words:
  the         87
  and         54
  of          41
  ...
```

## Done when
- [ ] Every function listed above exists and returns (not prints) its result
- [ ] Punctuation like `"Hello,"` and `hello` count as the same word
- [ ] A missing file is handled without crashing
- [ ] Numbers are printed with thousands separators (`f"{n:,}"`)

## Stretch goals
- Ignore common "stop words" (the, a, and, of, to...). Keep them in a `set` and explain why a set is better than a list for this.
- Count sentences and report the average sentence length.
- Print a simple horizontal bar chart of the top 10 words using `#` characters.
- Compare two files: which words appear in one but not the other? (set operations: `-`, `&`, `|`)

## Automated checks
The checks import your functions from `main.py`, so put them there, and keep the call to `main()` under `if __name__ == "__main__":`. The rules the checks assume:
- `clean_words` lowercases words, strips punctuation from them, and never returns empty strings. For example, `'"Hello," she said - twice.'` gives `["hello", "she", "said", "twice"]`.
- `top_n` and `longest_words` break ties alphabetically. `longest_words` returns the longest word first.
- `average_word_length([])` returns `0.0`.
- `word_frequencies` must not use `collections.Counter`.
- `main()` keeps asking for a filename until it gets one that exists.

```powershell
python -m pytest spec_tests -v
```

## Reflect
Can you call `word_frequencies` from the Python REPL (just type `python`) with your own list, without running the whole program? That's the payoff of writing pure functions, and it sets you up for testing in project 07.
