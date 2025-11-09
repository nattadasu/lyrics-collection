#!/usr/bin/env python3
"""
Lyrics linter based on Musixmatch lyric guidelines.
Reference: https://community.musixmatch.com/guidelines?lng=en#format
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import ass

# Error code definitions
ERROR_CODES = {
    # Parse errors
    "MX000": {"message": "Failed to parse ASS file", "level": "error"},
    # Capitalization (MX1XX)
    "MX101": {"message": "First letter must be capitalized", "level": "error"},
    "MX102": {"message": "Don't use all caps for emphasis", "level": "error"},
    "MX103": {"message": "Don't capitalize every word (title case)", "level": "error"},
    # Punctuation (MX2XX)
    "MX201": {"message": "Don't end lines with commas", "level": "error"},
    "MX202": {
        "message": "Don't end lines with periods (unless acronym or ellipsis)",
        "level": "error",
    },
    "MX203": {"message": "Don't use multiple punctuation marks", "level": "error"},
    "MX204": {"message": "Remove space before punctuation", "level": "error"},
    "MX205": {"message": "Add space after punctuation", "level": "error"},
    # Formatting and line breaks (MX3XX)
    "MX301": {"message": "Remove multiple consecutive spaces", "level": "error"},
    "MX302": {"message": "Remove leading/trailing spaces", "level": "error"},
    "MX303": {
        "message": 'Use straight quotes (") instead of smart quotes',
        "level": "error",
    },
    "MX304": {
        "message": "Use Unicode ellipsis (…) instead of three dots (...)",
        "level": "warning",
    },
    "MX305": {
        "message": "Consider splitting multi-line lyrics into separate events",
        "level": "warning",
    },
    "MX306": {
        "message": "Don't use ASS override tags (except for any karaoke tags)",
        "level": "error",
    },
    # Special characters (MX4XX)
    "MX401": {"message": "Don't use square brackets [ ] in lyrics", "level": "error"},
    "MX402": {
        "message": "Don't censor with asterisks. Use hyphen if audio is censored (e.g., 'f-')",
        "level": "error",
    },
    # Numbers (MX5XX)
    "MX501": {
        "message": "Write numbers over 10 numerically, not as words",
        "level": "error",
    },
    # Multipliers (MX6XX)
    "MX601": {
        "message": "Don't use multipliers like (x5). Transcribe repetitions fully",
        "level": "error",
    },
    # Non-vocal content (MX7XX)
    "MX701": {
        "message": "Don't include structure labels like (Verse - Artist)",
        "level": "error",
    },
    "MX702": {
        "message": "Don't include sound effect descriptions like *dial tone*",
        "level": "error",
    },
    # Direct speech (MX8XX)
    "MX801": {
        "message": "Direct speech should follow a comma: 'text, \"Speech\"'",
        "level": "warning",
    },
    "MX802": {
        "message": "Direct speech must start with capital letter",
        "level": "error",
    },
}


class LintError:
    """Represents a linting error with code and details."""

    def __init__(
        self, code: str, line_num: int, context: str = "", full_line: str = ""
    ):
        self.code = code
        self.line_num = line_num
        self.context = context
        self.full_line = full_line

        if code not in ERROR_CODES:
            raise ValueError(f"Unknown error code: {code}")

        self.error_def = ERROR_CODES[code]
        self.is_warning = self.error_def["level"] == "warning"

    def to_dict(self) -> Dict[str, Any]:
        """Convert LintError to dictionary for JSON serialization."""
        return {
            "line": self.line_num,
            "code": self.code,
            "message": self.error_def["message"],
            "level": self.error_def["level"],
            "context": self.context,
            "full_line": self.full_line,
        }


class MusixmatchLyricsLinter:
    """Linter for ASS lyrics files following Musixmatch guidelines."""

    def __init__(self, file_path: Path, disabled_rules: Optional[Set[str]] = None):
        self.file_path = file_path
        self.lint_errors: List[LintError] = []
        self.disabled_rules_global = disabled_rules or set()
        self.disabled_rules_file: Set[str] = set()
        self.enabled_rules_file: Set[str] = set()
        self.all_rules_disabled_file = False

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                self.doc = ass.parse(f)
        except Exception as e:
            self.lint_errors.append(LintError("MX000", 0, str(e)))
            self.doc = None

    def lint(self) -> Tuple[List[LintError], List[LintError]]:
        """Run all linting checks."""
        if self.doc is None:
            return self._format_output()

        self._process_all_events()

        return self._format_output()

    def _process_file_wide_directive(self, event: Any):
        """Process file-wide lint suppression directives from Comment events."""
        if type(event).__name__ != "Comment":
            return

        effect = event.effect.strip().lower() if hasattr(event, "effect") else ""
        text = self.strip_ass_tags(event.text).strip() if hasattr(event, "text") else ""

        if effect == "lint-disable":
            if not text:
                self.all_rules_disabled_file = True
            else:
                rules = [r.upper() for r in text.split()]
                self.disabled_rules_file.update(rules)
        elif effect == "lint-enable":
            if not text:
                self.all_rules_disabled_file = False
                self.disabled_rules_file.clear()
            else:
                rules = [r.upper() for r in text.split()]
                self.enabled_rules_file.update(rules)
                self.disabled_rules_file.difference_update(rules)

    def _is_rule_disabled(self, rule_code: str, line_suppressions: Set[str]) -> bool:
        """Check if a rule is disabled globally, file-wide, or on this line."""
        if self.all_rules_disabled_file and rule_code not in self.enabled_rules_file:
            return True
        if rule_code in self.disabled_rules_global:
            return True
        if (
            rule_code in self.disabled_rules_file
            and rule_code not in self.enabled_rules_file
        ):
            return True
        if rule_code in line_suppressions:
            return True
        return False

    def _get_line_suppressions(self, event: Any) -> Set[str]:
        """Extract suppression rules from the effect field (noqa or skip-XXX)."""
        suppressions: Set[str] = set()
        if not hasattr(event, "effect"):
            return suppressions

        effect = event.effect.strip()
        if not effect:
            return suppressions

        if effect.lower() == "noqa":
            return {"*"}

        parts = effect.split()
        for part in parts:
            if part.lower().startswith("skip-"):
                rule = part[5:].upper()
                suppressions.add(rule)

        return suppressions

    def _add_error(
        self,
        code: str,
        line_num: int,
        context: str,
        line_suppressions: Set[str],
        full_line: str = "",
    ):
        """Add a linting error if not suppressed."""
        if "*" in line_suppressions or self._is_rule_disabled(code, line_suppressions):
            return
        self.lint_errors.append(LintError(code, line_num, context, full_line))

    def _process_all_events(self):
        """Process all events in a single loop."""
        dialogue_line_num = 0

        for event in self.doc.events:
            # Process file-wide directives
            self._process_file_wide_directive(event)

            # Process dialogue events
            if type(event).__name__ != "Dialogue":
                continue

            dialogue_line_num += 1

            # Get text before ASS tag stripping for certain checks
            text_raw = re.sub(r"\{[^}]*\}", "", event.text)
            text_raw = text_raw.replace("\\N", " ").replace("\\n", " ")

            text = self.strip_ass_tags(event.text)
            if not text.strip():
                continue

            line_suppressions = self._get_line_suppressions(event)

            self._check_capitalization_line(dialogue_line_num, text, line_suppressions)
            self._check_punctuation_line(dialogue_line_num, text, line_suppressions)
            self._check_formatting_line(
                dialogue_line_num, text, text_raw, line_suppressions
            )
            self._check_special_characters_line(
                dialogue_line_num, text, line_suppressions
            )
            self._check_line_breaks_line(
                dialogue_line_num, text, event.text, line_suppressions
            )
            self._check_numbers_line(dialogue_line_num, text, line_suppressions)
            self._check_multipliers_line(dialogue_line_num, text, line_suppressions)
            self._check_censorship_line(dialogue_line_num, text, line_suppressions)
            self._check_non_vocal_content_line(
                dialogue_line_num, text, line_suppressions, event.text
            )
            self._check_direct_speech_line(dialogue_line_num, text, line_suppressions)

    def _format_output(self) -> Tuple[List["LintError"], List["LintError"]]:
        """Format errors and warnings for output."""
        errors = [e for e in self.lint_errors if not e.is_warning]
        warnings = [e for e in self.lint_errors if e.is_warning]
        return errors, warnings

    def _check_capitalization_line(
        self, line_num: int, text: str, suppressions: Set[str]
    ):
        """Check capitalization rules for a single line."""
        has_case_system = any(c.isupper() or c.islower() for c in text if c.isalpha())

        if not has_case_system:
            return

        # MX101: First letter must be capitalized
        first_alpha = next((c for c in text if c.isalpha()), None)
        if first_alpha and not first_alpha.isupper() and not first_alpha.islower():
            pass
        elif text and text[0].isalpha() and not text[0].isupper():
            if not any(text.startswith(p) for p in ["iPhone", "iPad", "eBay"]):
                self._add_error("MX101", line_num, text[0], suppressions, text)

        # MX102: Don't use all caps for emphasis
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
            self._add_error(
                "MX102", line_num, " ".join(all_caps_words), suppressions, text
            )

        # MX103: Don't capitalize every word (title case)
        words_longer_than_3 = [w for w in words if len(w) > 3 and w.isalpha()]
        if len(words_longer_than_3) > 2:
            title_case_count = sum(1 for w in words_longer_than_3 if w[0].isupper())
            if title_case_count == len(words_longer_than_3):
                self._add_error(
                    "MX103", line_num, " ".join(words_longer_than_3), suppressions, text
                )

    def _check_punctuation_line(self, line_num: int, text: str, suppressions: Set[str]):
        """Check punctuation rules for a single line."""
        rstrip = text.rstrip()

        # MX201: Don't end lines with commas
        if rstrip.endswith(",") or rstrip.endswith("、"):
            self._add_error("MX201", line_num, rstrip[-1], suppressions, text)

        # MX202: Don't end lines with periods (except acronyms and ellipses)
        if (rstrip.endswith(".") or rstrip.endswith("。")) and not re.search(
            r"[A-Z]\.$|\.{3}$", rstrip
        ):
            self._add_error("MX202", line_num, rstrip[-1], suppressions, text)

        # MX203: Don't use multiple punctuation marks
        match = re.search(
            r"(?<!\.)\.\.(?!\.)|\.{4,}|[!?]{2,}|[!?]\.(?!\.)|\.\.?[!?]", text
        )
        if match:
            self._add_error("MX203", line_num, match.group(), suppressions, text)

        # MX204: Remove space before punctuation
        match = re.search(r"\s+[,.!?;:]", text)
        if match:
            self._add_error("MX204", line_num, match.group(), suppressions, text)

        # MX205: Add space after punctuation
        match = re.search(r"[,.!?;:][a-zA-Z]", text)
        if match:
            self._add_error("MX205", line_num, match.group(), suppressions, text)

    def _check_formatting_line(
        self, line_num: int, text: str, text_raw: str, suppressions: Set[str]
    ):
        """Check text formatting rules for a single line."""
        # MX301: Remove multiple consecutive spaces (check before strip_ass_tags normalization)
        if "  " in text_raw:
            match = re.search(r"  +", text_raw)
            self._add_error(
                "MX301", line_num, match.group() if match else "  ", suppressions, text
            )

        # MX302: Remove leading/trailing spaces (check before strip_ass_tags normalization)
        if text_raw != text_raw.strip():
            self._add_error("MX302", line_num, "", suppressions, text)

        # MX303: Use straight quotes instead of smart quotes
        smart_quote_chars = '""""'
        smart_quotes = [c for c in text if c in smart_quote_chars]
        if smart_quotes:
            self._add_error(
                "MX303", line_num, "".join(smart_quotes), suppressions, text
            )

        # MX304: Use Unicode ellipsis instead of three dots
        match = re.search(r"\.{3}", text)
        if match:
            self._add_error("MX304", line_num, match.group(), suppressions, text)

    def _check_special_characters_line(
        self, line_num: int, text: str, suppressions: Set[str]
    ):
        """Check for special characters and symbols for a single line."""
        # MX401: Don't use brackets in lyrics
        if "[" in text or "]" in text:
            brackets = "".join([c for c in text if c in "[]"])
            self._add_error("MX401", line_num, brackets, suppressions, text)

        # MX402: Don't censor with asterisks (merged from old MX401 and MX801)
        match = re.search(r"\*\*+", text)
        if match:
            self._add_error("MX402", line_num, match.group(), suppressions, text)

    def _check_line_breaks_line(
        self, line_num: int, text: str, raw_text: str, suppressions: Set[str]
    ):
        """Check line break rules for a single line."""
        # MX305: Consider splitting multi-line lyrics
        if "\\N" in raw_text or "\\n" in raw_text:
            self._add_error("MX305", line_num, "", suppressions, text)

    def _check_numbers_line(self, line_num: int, text: str, suppressions: Set[str]):
        """Check number formatting for a single line."""
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

        text_lower = text.lower()

        # MX501: Write numbers over 10 numerically
        for word, value in number_words.items():
            if value > 10:
                match = re.search(rf"\b{word}\b", text_lower)
                if match:
                    self._add_error("MX501", line_num, word, suppressions, text)
                    break

    def _check_multipliers_line(self, line_num: int, text: str, suppressions: Set[str]):
        """Check for multipliers for a single line."""
        # MX601: Don't use multipliers
        match = re.search(r"\([xX×]\s*\d+\)", text)
        if match:
            self._add_error("MX601", line_num, match.group(), suppressions, text)

    def _check_censorship_line(self, line_num: int, text: str, suppressions: Set[str]):
        """Check censorship formatting for a single line."""
        # Note: Censorship check now merged into MX402 in _check_special_characters_line
        pass

    def _check_non_vocal_content_line(
        self, line_num: int, text: str, suppressions: Set[str], raw_text: str = ""
    ):
        """Check for non-vocal content for a single line."""
        # MX701: Don't include structure labels
        match = re.search(
            r"\((Verse|Chorus|Bridge|Intro|Outro|Hook|Pre-Chorus)[\s\-][^)]*\)",
            text,
            re.IGNORECASE,
        )
        if match:
            self._add_error("MX701", line_num, match.group(), suppressions, text)

        # MX702: Don't include sound effect descriptions
        match = re.search(r"\*[^*]+\*", text)
        if match:
            self._add_error("MX702", line_num, match.group(), suppressions, text)

        # MX306: Don't use ASS override tags (except karaoke tags)
        if raw_text:
            # Find all ASS override tags
            for match in re.finditer(r"\{\\[^}]+\}", raw_text):
                tag_content = match.group()
                # Allow karaoke tags: \k, \K, \kf, \ko, etc.
                if not re.search(r"\\[kK]", tag_content):
                    self._add_error(
                        "MX306", line_num, tag_content, suppressions, raw_text
                    )

    def _check_direct_speech_line(
        self, line_num: int, text: str, suppressions: Set[str]
    ):
        """Check direct speech formatting for a single line."""
        if '"' not in text:
            return

        # MX801: Direct speech should follow a comma (warning)
        match = re.search(r'"[A-Z]', text)
        if match and not re.search(r',\s*"[A-Z]', text):
            if not text.strip().startswith('"'):
                self._add_error("MX801", line_num, match.group(), suppressions, text)

        # MX802: Direct speech must start with capital letter
        quotes = re.findall(r'"([^"]+)"', text)
        for quote in quotes:
            if quote and quote[0].isalpha() and not quote[0].isupper():
                self._add_error("MX802", line_num, f'"{quote}"', suppressions, text)

    @staticmethod
    def strip_ass_tags(text: str) -> str:
        """Remove ASS formatting tags from text."""
        text = re.sub(r"\{[^}]*\}", "", text)
        text = text.replace("\\N", " ").replace("\\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()


def list_error_codes():
    """Print all available error codes and their descriptions."""
    from rich import box
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # Define categories based on code ranges
    def get_category(code: str) -> str:
        if code == "MX000":
            return "Parse Errors"
        elif code.startswith("MX1"):
            return "Capitalization"
        elif code.startswith("MX2"):
            return "Punctuation"
        elif code.startswith("MX3"):
            return "Formatting & Line Breaks"
        elif code.startswith("MX4"):
            return "Special Characters"
        elif code.startswith("MX5"):
            return "Numbers"
        elif code.startswith("MX6"):
            return "Multipliers"
        elif code.startswith("MX7"):
            return "Non-Vocal Content"
        elif code.startswith("MX8"):
            return "Direct Speech"
        else:
            return "Other"

    table = Table(
        title="Lint Error Codes",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Code", style="cyan", width=8)
    table.add_column("Category", style="blue", width=25)
    table.add_column("Level", width=8)
    table.add_column("Message", style="white")

    sorted_codes = sorted(ERROR_CODES.keys())
    for i, code in enumerate(sorted_codes):
        error_def = ERROR_CODES[code]
        category = get_category(code)

        level_style = "red" if error_def["level"] == "error" else "yellow"

        # Check if next item has different category (draw separator after this row)
        add_section = False
        if i + 1 < len(sorted_codes):
            next_code = sorted_codes[i + 1]
            next_category = get_category(next_code)
            add_section = category != next_category

        table.add_row(
            code,
            category,
            f"[{level_style}]{error_def['level'].upper()}[/{level_style}]",
            error_def["message"],
            end_section=add_section,
        )

    console.print(table)


def main():
    """Main function to lint all ASS files."""
    import argparse

    from rich import box
    from rich.console import Console
    from rich.table import Table

    console = Console()

    parser = argparse.ArgumentParser(
        description="Lint ASS lyrics files following Musixmatch guidelines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Lint all files in ass/ directory
  %(prog)s file1.ass file2.ass       # Lint specific files
  %(prog)s --disable MX101 MX202     # Disable specific rules globally
  %(prog)s --disable MX101           # Disable a single rule
  %(prog)s --json                    # Output results in JSON format
        """,
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="ASS files to lint (if not provided, lints all files in ass/ directory)",
    )
    parser.add_argument(
        "--disable",
        nargs="+",
        metavar="RULE",
        help="Disable specific linting rules (e.g., MX101 MX202)",
    )
    parser.add_argument(
        "--list-codes",
        action="store_true",
        help="List all available error codes and exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )

    args = parser.parse_args()

    # List error codes if requested
    if args.list_codes:
        list_error_codes()
        return

    # Parse disabled rules
    disabled_rules = set()
    if args.disable:
        disabled_rules = set(rule.upper() for rule in args.disable)

    # Get list of files to lint
    if args.files:
        ass_files = [Path(f) for f in args.files if f.endswith(".ass")]
    else:
        ass_dir = Path("ass")
        if not ass_dir.exists():
            console.print(f"[red]Error:[/red] Directory '{ass_dir}' not found")
            sys.exit(1)
        ass_files = list(ass_dir.rglob("*.ass"))

    if not ass_files:
        console.print("[yellow]No ASS files found[/yellow]")
        return

    if not args.json:
        console.print(f"[cyan]Linting {len(ass_files)} ASS file(s)...[/cyan]")
        if disabled_rules:
            console.print(
                f"[dim]Disabled rules: {', '.join(sorted(disabled_rules))}[/dim]\n"
            )

    total_errors = 0
    total_warnings = 0
    files_with_issues = 0
    all_issues = []

    for ass_file in sorted(ass_files):
        linter = MusixmatchLyricsLinter(ass_file, disabled_rules)
        errors, warnings = linter.lint()

        if errors or warnings:
            files_with_issues += 1
            all_issues.append((ass_file, errors, warnings))
            total_errors += len(errors)
            total_warnings += len(warnings)

    # JSON output
    if args.json:
        output = {
            "summary": {
                "files_checked": len(ass_files),
                "files_with_issues": files_with_issues,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
            },
            "files": [],
        }

        for ass_file, errors, warnings in all_issues:
            file_data = {
                "path": str(ass_file),
                "errors": [e.to_dict() for e in errors],
                "warnings": [w.to_dict() for w in warnings],
            }
            output["files"].append(file_data)

        print(json.dumps(output))
        sys.exit(1 if total_errors > 0 else 0)

    # Display issues grouped by file
    for ass_file, errors, warnings in all_issues:
        console.print(f"\n[bold cyan]📄 {ass_file}[/bold cyan]\n")

        # Group by line number for cleaner display
        issues_by_line = {}

        for error in errors:
            if error.line_num not in issues_by_line:
                issues_by_line[error.line_num] = []
            issues_by_line[error.line_num].append(error)

        for warning in warnings:
            if warning.line_num not in issues_by_line:
                issues_by_line[warning.line_num] = []
            issues_by_line[warning.line_num].append(warning)

        # Display issues line by line
        for line_num in sorted(issues_by_line.keys()):
            console.print(f"Line [bold cyan]{line_num}[/bold cyan]")
            for lint_error in issues_by_line[line_num]:
                issue_type = "warning" if lint_error.is_warning else "error"
                color = "red" if issue_type == "error" else "yellow"
                symbol = "✗" if issue_type == "error" else "⚠"
                code = lint_error.code
                lint_msg = lint_error.error_def["message"]
                highlighted_issue = lint_error.context
                full_line = lint_error.full_line

                # Show the full line with the highlighted issue
                if highlighted_issue and highlighted_issue in full_line:
                    # Find and highlight the issue in the full line before escaping
                    idx = full_line.find(highlighted_issue)
                    if idx != -1:
                        before = full_line[:idx].replace("[", "\\[").replace("]", "\\]")
                        issue = highlighted_issue.replace("[", "\\[").replace(
                            "]", "\\]"
                        )
                        after = (
                            full_line[idx + len(highlighted_issue) :]
                            .replace("[", "\\[")
                            .replace("]", "\\]")
                        )
                        line_with_highlight = (
                            f"{before}[bold {color}]{issue}[/bold {color}]{after}"
                        )
                        console.print(
                            f"  [{color}]{symbol} {code}[/{color}]: {line_with_highlight}",
                            highlight=False,
                        )
                    else:
                        # Fallback if not found
                        full_line_escaped = full_line.replace("[", "\\[").replace(
                            "]", "\\]"
                        )
                        console.print(
                            f"  [{color}]{symbol} {code}[/{color}]: {full_line_escaped}",
                            highlight=False,
                        )
                else:
                    # If no highlighted issue or can't find it, just show the full line
                    full_line_escaped = full_line.replace("[", "\\[").replace(
                        "]", "\\]"
                    )
                    console.print(
                        f"  [{color}]{symbol} {code}[/{color}]: {full_line_escaped}",
                        highlight=False,
                    )

                # Show the lint message below if available
                if lint_msg:
                    console.print(f"         [dim]> {lint_msg}[/dim]", highlight=False)

    # Summary
    console.print()
    summary_table = Table(
        title="[bold cyan]Linting Summary[/bold cyan]",
        show_header=False,
        box=box.ROUNDED,
        padding=(0, 1),
        expand=False,
    )
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Count", justify="right", no_wrap=True)

    summary_table.add_row("Files checked", str(len(ass_files)))
    summary_table.add_row("Files with issues", str(files_with_issues))

    if total_errors > 0:
        summary_table.add_row("Errors", f"[red bold]{total_errors}[/red bold]")
    else:
        summary_table.add_row("Errors", "[green]0[/green]")

    if total_warnings > 0:
        summary_table.add_row("Warnings", f"[yellow]{total_warnings}[/yellow]")
    else:
        summary_table.add_row("Warnings", "[green]0[/green]")

    console.print(summary_table)

    if total_errors > 0:
        console.print("\n[red bold]❌ Linting failed with errors[/red bold]")
        sys.exit(1)
    elif total_warnings > 0:
        console.print("\n[yellow]⚠️  Linting passed with warnings[/yellow]")
    else:
        console.print("\n[green bold]✅ All files passed linting![/green bold]")


if __name__ == "__main__":
    main()
