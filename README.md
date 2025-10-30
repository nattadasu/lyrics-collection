# lyrics-collection

A collection of ASS lyrics because all LRC editors were suck when playing ALAC...

## Requirements

- [Task](https://taskfile.dev/) - Task runner
- [uv](https://docs.astral.sh/uv/) - Python package manager
- Python 3.13+

## Setup

1. Install dependencies:

   ```bash
   task install
   ```

2. (Optional) Set up pre-commit hooks:

   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Usage

### Convert ASS to LRC

Convert all ASS files to simple LRC format:

```bash
task convert
```

Convert to enhanced LRC format (with word-level timing):

```bash
task convert:enhanced
```

### Lint Lyrics

Run the Musixmatch guidelines linter:

```bash
task lint
```

The linter checks for:

**Capitalization:**
- First letter of each line must be capitalized (skipped for lines starting with non-Latin scripts)
- No all-caps for emphasis (SHOUTING)
- No Title Case Every Word
- Parenthetical text only capitalized when grammatically appropriate

**Punctuation:**
- No commas at end of lines
- No periods at end of lines (unless acronyms)
- No multiple punctuation marks (!!, ??) - ellipses (...) are allowed
- Proper spacing around punctuation

**Numbers:**
- Numbers 11+ must be numeric (99, not ninety-nine)
- Numbers 1-10 should be words (one, two, three)

**Formatting:**
- No multipliers like (x5) - transcribe repetitions fully
- No censorship with asterisks (****) - use hyphen if audio censored (f-)
- No structure labels like (Verse - Artist)
- No sound effect descriptions like *dial tone*
- Direct speech must follow: `She said, "Hello there"`
- Use straight quotes (") not smart quotes (“”)

**Special Cases:**
- Scripts without case systems (Arabic, Chinese, Japanese) skip capitalization checks
- Common acronyms (DJ, TV, USA, UK) are allowed in caps

## License

This project is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](LICENSE).