#!/usr/bin/env python3
"""
Lyrics linter based on Musixmatch lyric guidelines.
Reference: https://community.musixmatch.com/guidelines?lng=en#format
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple
import ass


class MusixmatchLyricsLinter:
    """Linter for ASS lyrics files following Musixmatch guidelines."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.errors: List[str] = []
        self.warnings: List[str] = []

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                self.doc = ass.parse(f)
        except Exception as e:
            self.errors.append(f"Failed to parse ASS file: {e}")
            self.doc = None

    def lint(self) -> Tuple[List[str], List[str]]:
        """Run all linting checks."""
        if self.doc is None:
            return self.errors, self.warnings

        self.check_capitalization()
        self.check_punctuation()
        self.check_formatting()
        self.check_special_characters()
        self.check_line_breaks()
        self.check_numbers()
        self.check_multipliers()
        self.check_censorship()
        self.check_non_vocal_content()
        self.check_direct_speech()

        return self.errors, self.warnings

    def check_capitalization(self):
        """
        Check capitalization rules:
        - Capitalize first letter of each line
        - Capitalize all proper nouns
        - Capitalize after ? or !
        - Don't capitalize erratically or for emphasis
        - For parentheses: capitalize when grammatically appropriate
        """
        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue

            has_case_system = any(
                c.isupper() or c.islower() for c in text if c.isalpha()
            )

            if not has_case_system:
                continue

            # Check if first letter is capitalized
            # Skip if line starts with a script that doesn't have case (e.g., CJK, Arabic, etc.)
            first_alpha = next((c for c in text if c.isalpha()), None)
            if first_alpha and not first_alpha.isupper() and not first_alpha.islower():
                # Character doesn't have case distinction (e.g., CJK), skip check
                pass
            elif text and text[0].isalpha() and not text[0].isupper():
                if not any(text.startswith(p) for p in ["iPhone", "iPad", "eBay"]):
                    self.errors.append(
                        f"Line {i}: First letter must be capitalized: '{text}'"
                    )

            # Check for all caps words (SHOUTING) - not allowed for emphasis
            words = text.split()
            all_caps_words = [
                w
                for w in words
                if w.isupper()
                and len(w) > 1
                and w.isalpha()
                and w not in ["DJ", "TV", "USA", "UK", "NYC", "LA"]
            ]
            if len(all_caps_words) > 0:
                self.errors.append(
                    f"Line {i}: Don't use all caps for emphasis: '{text}'"
                )

            # Check for Title Case (Every Word Capitalized)
            words_longer_than_3 = [w for w in words if len(w) > 3 and w.isalpha()]
            if len(words_longer_than_3) > 2:
                title_case_count = sum(1 for w in words_longer_than_3 if w[0].isupper())
                if title_case_count == len(words_longer_than_3):
                    self.errors.append(
                        f"Line {i}: Don't capitalize every word (title case): '{text}'"
                    )

    def check_punctuation(self):
        """
        Check punctuation rules:
        - No commas at end of lines
        - No periods at end of lines (except acronyms)
        - Question marks and exclamation marks are fine in moderation
        - Hyphens only for interruptions
        - Ellipses only for fade outs
        """
        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue
            rstrip = text.rstrip()

            # Check for commas at end of line
            if rstrip.endswith(",") or rstrip("、"):
                self.errors.append(f"Line {i}: Don't end lines with commas: '{text}'")

            # Check for periods at end of line (except acronyms)
            if (rstrip.endswith(".") or rstrip.endswith("。")) and not re.search(
                r"[A-Z]\.$", rstrip
            ):
                self.errors.append(
                    f"Line {i}: Don't end lines with periods (unless acronym): '{text}'"
                )

            # Check for multiple punctuation marks (but allow ellipses - exactly 3 dots)
            # Match: two dots not followed by another, or 4+ dots, or multiple !?, or !?. combos
            if re.search(r"(?<!\.)\.\.(?!\.)|\.{4,}|[!?]{2,}|[!?]\.(?!\.)|\.\.?[!?]", text):
                self.errors.append(
                    f"Line {i}: Don't use multiple punctuation marks: '{text}'"
                )

            # Check for spaces before punctuation
            if re.search(r"\s+[,.!?;:]", text):
                self.errors.append(
                    f"Line {i}: Remove space before punctuation: '{text}'"
                )

            # Check for missing space after punctuation (except at end or before closing paren)
            if re.search(r"[,.!?;:][a-zA-Z]", text):
                self.errors.append(f"Line {i}: Add space after punctuation: '{text}'")

    def check_formatting(self):
        """Check text formatting rules."""
        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue

            # Check for multiple spaces
            if "  " in text:
                self.errors.append(
                    f"Line {i}: Remove multiple consecutive spaces: '{text}'"
                )

            # Check for leading/trailing spaces
            if text != text.strip():
                self.errors.append(f"Line {i}: Remove leading/trailing spaces")

            # Check for smart quotes vs straight quotes
            if '"' in text or '"' in text or """ in text or """ in text:
                self.errors.append(
                    f"Line {i}: Use straight quotes (\") instead of smart quotes: '{text}'"
                )

    def check_special_characters(self):
        """Check for special characters and symbols."""
        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue

            # Check for asterisks (censorship)
            if "*" in text and "****" in text:
                self.errors.append(
                    f"Line {i}: Don't censor with asterisks like ****. Only use if audio is censored: '{text}'"
                )

            # Check for brackets (not allowed)
            if "[" in text or "]" in text:
                self.errors.append(f"Line {i}: Don't use brackets in lyrics: '{text}'")

    def check_line_breaks(self):
        """
        Check line break rules:
        - Maximum 10 lines per section
        - Don't excessively transcribe vocalizations
        """
        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue

            # Check for line breaks within the text
            if "\\N" in event.text or "\\n" in event.text:
                self.warnings.append(
                    f"Line {i}: Consider splitting multi-line lyrics into separate events"
                )

            # Check for excessive vocalizations
            vocal_pattern = (
                r"^(ooh+|aah+|oh+|ah+|yeah+|uh+|eh+|mm+|la+|na+|da+)[\s\-,]*$"
            )
            if re.match(vocal_pattern, text.lower().strip()):
                # Count consecutive vocalizations
                pass  # This would need context from previous lines

    def check_numbers(self):
        """
        Check number formatting:
        - Write numbers 11+ numerically
        - Write numbers 1-10 as words
        - Phone numbers, dates, decades should be numeric
        - Exact times numeric (but not o'clock times)
        """
        number_words = {
            "eleven": 11,
            "twelve": 12,
            "thirteen": 13,
            "fourteen": 14,
            "fifteen": 15,
            "sixteen": 16,
            "seventeen": 17,
            "eighteen": 18,
            "nineteen": 19,
            "twenty": 20,
            "thirty": 30,
            "forty": 40,
            "fifty": 50,
            "sixty": 60,
            "seventy": 70,
            "eighty": 80,
            "ninety": 90,
            "hundred": 100,
            "thousand": 1000,
            "million": 1000000,
        }

        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue

            text_lower = text.lower()

            # Check for spelled out numbers > 10
            for word, value in number_words.items():
                if value > 10 and re.search(rf"\b{word}\b", text_lower):
                    self.errors.append(
                        f"Line {i}: Write numbers over 10 numerically, not as words: '{text}'"
                    )
                    break

    def check_multipliers(self):
        """
        Check for multipliers:
        - Multipliers like (x5) or (X5) are not allowed
        - Must transcribe repetitions fully
        """
        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue

            # Check for multiplier patterns
            if re.search(r"\([xX×]\s*\d+\)", text):
                self.errors.append(
                    f"Line {i}: Don't use multipliers like (x5). Transcribe repetitions fully: '{text}'"
                )

    def check_censorship(self):
        """
        Check censorship formatting:
        - Don't censor with ****
        - If audio is censored, use hyphen: f-
        """
        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue

            # Already checked in special_characters, but double check
            if re.search(r"\*\*+", text):
                self.errors.append(
                    f"Line {i}: Don't censor with asterisks. Use hyphen if audio is censored (e.g., 'f-'): '{text}'"
                )

    def check_non_vocal_content(self):
        """
        Check for non-vocal content:
        - No structure labels like (Verse - Artist)
        - No sound effect descriptions like *dial tone*
        """
        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue

            # Check for structure labels
            if re.search(
                r"\((Verse|Chorus|Bridge|Intro|Outro|Hook|Pre-Chorus)[\s\-]",
                text,
                re.IGNORECASE,
            ):
                self.errors.append(
                    f"Line {i}: Don't include structure labels like (Verse - Artist): '{text}'"
                )

            # Check for sound effects with asterisks
            if re.search(r"\*[^*]+\*", text):
                self.errors.append(
                    f"Line {i}: Don't include sound effect descriptions like *dial tone*: '{text}'"
                )

    def check_direct_speech(self):
        """
        Check direct speech formatting:
        - Should follow: Text, "Direct speech"
        - First letter of direct speech should be capitalized
        """
        for i, event in enumerate(self.doc.events, 1):
            if type(event).__name__ != "Dialogue":
                continue

            text = self.strip_ass_tags(event.text)

            if not text.strip():
                continue

            # Check for quotes
            if '"' in text:
                # Check format: should have comma before quote
                if re.search(r'"[A-Z]', text) and not re.search(r',\s*"[A-Z]', text):
                    # Check if it's at the start of the line
                    if not text.strip().startswith('"'):
                        self.warnings.append(
                            f"Line {i}: Direct speech should follow a comma: 'text, \"Speech\"': '{text}'"
                        )

                # Check if quoted text starts with capital
                quotes = re.findall(r'"([^"]+)"', text)
                for quote in quotes:
                    if quote and quote[0].isalpha() and not quote[0].isupper():
                        self.errors.append(
                            f"Line {i}: Direct speech must start with capital letter: '\"{quote}\"'"
                        )

    @staticmethod
    def strip_ass_tags(text: str) -> str:
        """Remove ASS formatting tags from text."""
        text = re.sub(r"\{[^}]*\}", "", text)
        text = text.replace("\\N", " ").replace("\\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()


def main():
    """Main function to lint all ASS files."""
    # Check if specific files were provided as arguments
    if len(sys.argv) > 1:
        ass_files = [Path(arg) for arg in sys.argv[1:] if arg.endswith(".ass")]
    else:
        ass_dir = Path("ass")

        if not ass_dir.exists():
            print(f"Error: Directory '{ass_dir}' not found")
            sys.exit(1)

        ass_files = list(ass_dir.rglob("*.ass"))

    if not ass_files:
        print(f"No ASS files found in '{ass_dir}'")
        return

    print(f"Linting {len(ass_files)} ASS file(s)...\n")

    total_errors = 0
    total_warnings = 0
    files_with_issues = 0

    for ass_file in sorted(ass_files):
        linter = MusixmatchLyricsLinter(ass_file)
        errors, warnings = linter.lint()

        if errors or warnings:
            files_with_issues += 1
            print(f"📄 {ass_file}")

            for error in errors:
                print(f"  ❌ ERROR: {error}")
                total_errors += 1

            for warning in warnings:
                print(f"  ⚠️  WARNING: {warning}")
                total_warnings += 1

            print()

    # Summary
    print("=" * 60)
    print("Linting complete!")
    print(f"Files checked: {len(ass_files)}")
    print(f"Files with issues: {files_with_issues}")
    print(f"Total errors: {total_errors}")
    print(f"Total warnings: {total_warnings}")

    if total_errors > 0:
        print("\n❌ Linting failed with errors")
        sys.exit(1)
    elif total_warnings > 0:
        print("\n⚠️  Linting passed with warnings")
    else:
        print("\n✅ All files passed linting!")


if __name__ == "__main__":
    main()
