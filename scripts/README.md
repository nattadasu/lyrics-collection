# Project's Scripts Documentations

## Lyrics Linter

A comprehensive linter for ASS subtitle files containing lyrics, based on
[Musixmatch lyric guidelines](https://community.musixmatch.com/guidelines?lng=en#format).

### Features

- ✅ **Codified Error Codes**: Unique codes (MX000-MX9XX) for easy reference
- ✅ **Rich Terminal Output**: Color-coded output with highlighted issues
- ✅ **JSON Output**: Machine-readable format for CI/CD integration
- ✅ **Flexible Suppression**: Line-level, file-wide, or global rule disabling
- ✅ **Single-Pass Processing**: Efficient scanning with grouped display

### Usage

```bash
# Lint all ASS files in the ass/ directory
python scripts/lint_lyrics.py

# Lint specific files
python scripts/lint_lyrics.py file1.ass file2.ass

# JSON output for automation
python scripts/lint_lyrics.py --json

# Disable specific rules
python scripts/lint_lyrics.py --disable MX101 MX202

# List all error codes
python scripts/lint_lyrics.py --list-codes
```

### Error Codes Reference

#### Quick Reference

| Category | Codes | Examples |
|----------|-------|----------|
| Parse Errors | MX000 | File parsing issues |
| Capitalization | MX1XX | First letter, all caps, title case |
| Punctuation | MX2XX | Commas, periods, multiple marks, spacing |
| Formatting & Line Breaks | MX3XX | Spaces, quotes, multi-line lyrics, ASS tags |
| Special Characters | MX4XX | Brackets, asterisks |
| Numbers | MX5XX | Spell out 1-10 only |
| Multipliers | MX6XX | No (x3) notations |
| Non-Vocal | MX7XX | Structure labels, sound effects |
| Direct Speech | MX8XX | Comma before quotes, capitalize |

#### MX000: Parse Error
Failed to parse the ASS file. Ensure the file is a valid ASS subtitle file.

#### MX1XX: Capitalization
| Code | Rule | Bad Example | Good Example |
|------|------|-------------|--------------|
| MX101 | First letter must be capitalized (skipped for non-Latin scripts) | `the world` | `The world` |
| MX102 | No all caps for emphasis (DJ, TV, USA, UK, NYC, LA excepted) | `I LOVE you` | `I love you` |
| MX103 | No title case | `Every Single Word` | `Every single word` |

> [!NOTE]
>
> - Capitalization checks are skipped for scripts without a case system
>   (e.g., Arabic, Chinese, Japanese)
> - Brand names like "iPhone", "iPad", "eBay" are allowed to start with lowercase letters

#### MX2XX: Punctuation
| Code | Rule | Bad Example | Good Example |
|------|------|-------------|--------------|
| MX201 | No trailing commas (including Japanese 、) | `I love you,` or `愛してる、` | `I love you` or `愛してる` |
| MX202 | No trailing periods (except acronyms) (including Japanese 。) | `I love you.` or `愛してる。` | `I love you` or `U.S.A.` or `愛してる` |
| MX203 | No multiple punctuation (ellipses `...` excepted) | `What??` or `Really?!` | `What?` or `Fading...` |
| MX204 | No space before punctuation | `Hello , world` | `Hello, world` |
| MX205 | Space after punctuation | `Hello,world` | `Hello, world` |

#### MX3XX: Formatting & Line Breaks
| Code | Rule | Bad Example | Good Example |
|------|------|-------------|--------------|
| MX301 | Single spaces only | `Hello··world` | `Hello world` |
| MX302 | No leading/trailing spaces | `·Hello·` | `Hello` |
| MX303 | Use straight quotes, not smart quotes | `"Hello"` | `"Hello"` |
| MX304 | Use Unicode ellipsis instead of three dots (Warning) | `Fading...` | `Fading…` |
| MX305 | Avoid `\N` or `\n` (Warning) | `Line one\NLine two` | Separate events |
| MX306 | No ASS override tags (karaoke tags like `\k`, `\K`, `\kf`, `\ko` are allowed) | `{\i1}Hello{\i0}` or `{\b1}World` | `Hello` or use karaoke tags only |

#### MX4XX: Special Characters
| Code | Rule | Bad Example | Good Example |
|------|------|-------------|--------------|
| MX401 | No square brackets | `[Verse] Hello` | `Hello` |
| MX402 | No asterisk censoring (use hyphens if audio is censored) | `F***` or `****` | `Fuck` or `F-` |

#### MX5XX: Numbers
| Code | Rule | Bad Example | Good Example |
|------|------|-------------|--------------|
| MX501 | Write 11+ as digits (1-10 can be words) | `twenty dollars` | `20 dollars` or `five dollars` |

#### MX6XX: Multipliers
| Code | Rule | Bad Example | Good Example |
|------|------|-------------|--------------|
| MX601 | No multipliers, transcribe fully | `La (x3)` | `La la la` |

#### MX7XX: Non-Vocal Content
| Code | Rule | Bad Example | Good Example |
|------|------|-------------|--------------|
| MX701 | No structure labels | `(Verse - John)` or `(Chorus)` | Remove labels |
| MX702 | No sound effects | `*dial tone* Hello` | `Hello` |

#### MX8XX: Direct Speech
| Code | Rule | Bad Example | Good Example |
|------|------|-------------|--------------|
| MX801 | Comma before quotes (Warning) | `She said "hi"` | `She said, "hi"` |
| MX802 | Capitalize quoted text | `"hello world"` | `"Hello world"` |

### Rule Suppression

#### Line-Level Suppression

Use the `Effect` field in ASS Dialogue lines:

```
# Suppress all rules
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,noqa,the world is mine

# Suppress specific rules (space-separated)
Dialogue: 0,0:00:03.00,0:00:05.00,Default,,0,0,0,skip-MX101,iPhone is great
Dialogue: 0,0:00:05.00,0:00:07.00,Default,,0,0,0,skip-MX101 skip-MX102,the LOUD music
```

#### File-Wide Suppression

Use Comment lines with `lint-disable` or `lint-enable` in the `Effect` field:

```
# Disable specific rules
Comment: 0,0:00:00.00,0:00:00.01,Default,,0,0,0,lint-disable,MX101 MX202

# Disable all rules (empty Text field)
Comment: 0,0:00:00.00,0:00:00.01,Default,,0,0,0,lint-disable,

# Re-enable specific rules
Comment: 0,0:00:00.00,0:00:00.01,Default,,0,0,0,lint-enable,MX101 MX202

# Re-enable all rules (empty Text field)
Comment: 0,0:00:00.00,0:00:00.01,Default,,0,0,0,lint-enable,
```

**Example:**

```
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Comment: 0,0:00:00.00,0:00:00.01,Default,,0,0,0,lint-disable,MX101 MX202
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,the world is mine.
Comment: 0,0:00:05.00,0:00:05.01,Default,,0,0,0,lint-enable,MX101
Dialogue: 0,0:00:06.00,0:00:08.00,Default,,0,0,0,,The world is mine.
Comment: 0,0:00:08.00,0:00:08.01,Default,,0,0,0,lint-enable,
Dialogue: 0,0:00:09.00,0:00:11.00,Default,,0,0,0,,The world is mine
```

1. Lines after first Comment can use lowercase and periods
2. After second Comment, capitalization required but periods still allowed
3. After third Comment, all rules apply

#### Global Suppression

Disable rules via command line for all files:

```bash
python scripts/lint_lyrics.py --disable MX101 MX202 MX303
```

### JSON Output

Use `--json` flag for machine-readable output:

```json
{
  "summary": {
    "files_checked": 1,
    "files_with_issues": 1,
    "total_errors": 2,
    "total_warnings": 1
  },
  "files": [
    {
      "path": "example.ass",
      "errors": [
        {
          "line": 1,
          "code": "MX101",
          "message": "First letter must be capitalized",
          "level": "error",
          "context": "h",
          "full_line": "hello world"
        }
      ],
      "warnings": [
        {
          "line": 2,
          "code": "MX901",
          "message": "Direct speech should follow a comma",
          "level": "warning",
          "context": "\"H",
          "full_line": "She said \"Hello\""
        }
      ]
    }
  ]
}
```

### Notes

- Warnings (⚠️) don't cause failure
- Errors (❌) cause exit code 1
- Suppression precedence: line-level > file-wide > global
- Rule codes are case-insensitive (MX101 = mx101)

