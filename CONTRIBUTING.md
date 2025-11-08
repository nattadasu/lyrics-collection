# Contributing to lyrics-collection

We welcome contributions to this collection! If you'd like to add new lyrics
or fix existing ones, please follow these guidelines.

## Getting Started

This project uses a few tools to maintain code quality and automate tasks.

### Requirements

- [Task](https://taskfile.dev/) - A task runner
- [uv](https://docs.astral.sh/uv/) - A Python package manager
- Python 3.13+

#### Recommendation

Use Aegisub to create and edit ASS files.

### Setup

1. Install dependencies:
   ```bash
   task install
   ```

2. Set up pre-commit hooks to automatically lint your changes:
   ```bash
   pre-commit install
   ```

## How to Add Lyrics

1. **Create an `.ass` file:** Place your new lyrics file in the `ass/`
   directory. Please follow the existing folder structure:
   `ass/<Album Artists, semicolon-delimiter>/<Album>/<Track>.ass`.
2. **Convert to LRC:** After adding your file, run the conversion script to
   generate the corresponding LRC file.
   ```bash
   # For simple LRC
   task convert

   # For word-level timing (Enhanced LRC)
   task convert:enhanced
   ```
   The new `.lrc` file will be created in the `compiled/` directory. For
   compatibility, we will only serve line-timed files instead.
3. **Lint your lyrics:** Run the linter to ensure your contribution meets
   the collection's formatting standards.
   ```bash
   task lint
   ```
   As this utilize custom script to check and warn stylistic error, please
   issued a bug whenever an unintended error has been issued. You can also
   add `noqa` keyword to effect field if needed, but not recommended.
4. **Submit a Pull Request:** Once all checks pass, commit your changes and
   open a pull request.

## Lyric Formatting Guidelines

To maintain consistency and quality, all contributed lyrics must adhere to
the following rules, which are based on the Musixmatch guidelines.
The `task lint` command will check for most of these automatically.

### Capitalization
- The first letter of each line must be capitalized (this is skipped for lines
  that do not start with a Latin script).
- Do not use all-caps for emphasis (SHOUTING).
- Do not use Title Case for every word.
- Text within parentheses should only be capitalized if it's a grammatically
  complete sentence.

### Punctuation
- Do not use commas at the end of lines.
- Do not use periods at the end of lines (unless it's part of an acronym).
- Avoid multiple consecutive punctuation marks (e.g., `!!`, `??`). Ellipses
  (`...`) are an exception.
- Ensure there is proper spacing around punctuation.

### Numbers
- Numbers from 11 and up should be written as digits (e.g., `99`).
- Numbers from one to ten should be written as words (e.g., `one`, `two`,
  `three`).

### Formatting
- Transcribe repetitions fully. Do not use multipliers like `(x5)`.
- Do not censor words with asterisks (`****`). If the audio is censored, use
  a hyphen (e.g., `f-`).
- Do not include structure labels like `(Verse - Artist)`.
- Do not include descriptions of sound effects like `*dial tone*`.
- Direct speech must be enclosed in straight quotes: `She said, "Hello there"`.
  Do not use smart quotes (`“”`).

### Special Cases
- Capitalization checks are skipped for scripts without a case system (e.g.,
  Arabic, Chinese, Japanese).
- Common acronyms like `DJ`, `TV`, `USA`, and `UK` are permitted to be in uppercase.
