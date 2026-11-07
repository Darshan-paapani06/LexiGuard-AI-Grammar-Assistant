"""Fast, deterministic grammar checks; optional LanguageTool extension."""
from __future__ import annotations
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any

@dataclass
class Suggestion:
    id: str
    start: int
    end: int
    original: str
    replacement: str
    message: str
    category: str
    severity: str = "medium"
    source: str = "Built-in"

# Rules are intentionally conservative: a suggestion should be better than a false fix.
PATTERNS = [
    (r"\b([Ii])\s+([Aa][Mm])\b", lambda m: "I am", "Use consistent capitalization.", "Grammar"),
    (r"\b([Ii])\s+([Ii])\b", lambda m: "I", "Avoid repeating a word.", "Clarity"),
    (r"\b([Tt])he\s+the\b", lambda m: m.group(1) + "he", "Remove the repeated article.", "Grammar"),
    (r"\b([Aa])\s+(?=[aeiouAEIOU])", lambda m: "An " if m.group(1).isupper() else "an ", "Use ‘an’ before a vowel sound (check exceptions manually).", "Grammar"),
    (r"\b([Aa])n\s+(?=[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ])", lambda m: "A " if m.group(1).isupper() else "a ", "Use ‘a’ before a consonant sound (check exceptions manually).", "Grammar"),
    (r"\b([Ii])\b", lambda m: "I", "Capitalize the pronoun ‘I’.", "Grammar"),
    (r"\b(dont|doesnt|didnt|cant|wont|isnt|arent|wasnt|werent|couldnt|shouldnt|wouldnt)\b", lambda m: {"dont":"don't", "doesnt":"doesn't", "didnt":"didn't", "cant":"can't", "wont":"won't", "isnt":"isn't", "arent":"aren't", "wasnt":"wasn't", "werent":"weren't", "couldnt":"couldn't", "shouldnt":"shouldn't", "wouldnt":"wouldn't"}[m.group().lower()].capitalize() if m.group()[0].isupper() else {"dont":"don't", "doesnt":"doesn't", "didnt":"didn't", "cant":"can't", "wont":"won't", "isnt":"isn't", "arent":"aren't", "wasnt":"wasn't", "werent":"weren't", "couldnt":"couldn't", "shouldnt":"shouldn't", "wouldnt":"wouldn't"}[m.group().lower()], "Add the missing apostrophe.", "Spelling"),
    (r"\b(teh|recieve|seperate|definately|occured|goverment|grammer|wierd|adress|acheive|becuase|thier|langauge|enviroment)\b", lambda m: {"teh":"the","recieve":"receive","seperate":"separate","definately":"definitely","occured":"occurred","goverment":"government","grammer":"grammar","wierd":"weird","adress":"address","acheive":"achieve","becuase":"because","thier":"their","langauge":"language","enviroment":"environment"}[m.group().lower()].capitalize() if m.group()[0].isupper() else {"teh":"the","recieve":"receive","seperate":"separate","definately":"definitely","occured":"occurred","goverment":"government","grammer":"grammar","wierd":"weird","adress":"address","acheive":"achieve","becuase":"because","thier":"their","langauge":"language","enviroment":"environment"}[m.group().lower()], "Correct a common spelling mistake.", "Spelling"),
    (r"\b(very very|really really)\b", lambda m: m.group().split()[0], "Avoid repeating an intensifier.", "Clarity"),
    (r" {2,}", lambda m: " ", "Remove extra spaces.", "Punctuation"),
    (r"\s+([,;:.!?])", lambda m: m.group(1), "Remove the space before punctuation.", "Punctuation"),
    (r"([!?.,])\1{1,}", lambda m: m.group(1), "Avoid repeated punctuation.", "Punctuation"),
    (r"\b([Tt])his\s+is\s+are\b", lambda m: "This is" if m.group(1).isupper() else "this is", "Remove the extra verb.", "Grammar"),
    (r"\b([Hh])e\s+go\s+to\b", lambda m: "He goes to" if m.group(1).isupper() else "he goes to", "Match the verb to a singular subject.", "Grammar"),
    (r"\b([Ss])he\s+go\s+to\b", lambda m: "She goes to" if m.group(1).isupper() else "she goes to", "Match the verb to a singular subject.", "Grammar"),
    (r"\b([Hh])e\s+have\b", lambda m: "He has" if m.group(1).isupper() else "he has", "Use ‘has’ with a singular subject.", "Grammar"),
    (r"\b([Ss])he\s+have\b", lambda m: "She has" if m.group(1).isupper() else "she has", "Use ‘has’ with a singular subject.", "Grammar"),
    (r"\b([Tt])hey\s+is\b", lambda m: "They are" if m.group(1).isupper() else "they are", "Use ‘are’ with a plural subject.", "Grammar"),
]
COMPILED = [(re.compile(p, flags=re.IGNORECASE), f, msg, cat) for p, f, msg, cat in PATTERNS]

def collect(text: str) -> list[Suggestion]:
    candidates: list[Suggestion] = []
    for regex, replacement_fn, message, category in COMPILED:
        for m in regex.finditer(text):
            replacement = replacement_fn(m)
            if replacement == m.group():
                continue
            candidates.append(Suggestion("", m.start(), m.end(), m.group(), replacement, message, category))
    # Capitalization of first letter in a sentence (skip quoted punctuation).
    for match in re.finditer(r"(^|[.!?]\s+)([a-z])", text):
        pos = match.start(2)
        candidates.append(Suggestion("", pos, pos + 1, text[pos], text[pos].upper(), "Start sentences with a capital letter.", "Grammar"))
    # Add punctuation only for prose longer than two words, ending with a letter.
    if len(text.split()) >= 3 and re.search(r"[A-Za-z]$", text.rstrip()):
        pos = len(text.rstrip())
        candidates.append(Suggestion("", pos, pos, "", ".", "Consider ending the sentence with punctuation.", "Punctuation", "low"))
    # Reject overlapping ranges; deterministic precedence by earliest start / longest match.
    candidates.sort(key=lambda s: (s.start, -(s.end - s.start)))
    selected: list[Suggestion] = []
    for s in candidates:
        if any(s.start < x.end and x.start < s.end or (s.start == x.start and s.end == x.end) for x in selected):
            continue
        s.id = f"s{len(selected)+1}"
        selected.append(s)
    return selected

def apply_suggestions(text: str, suggestions: list[dict[str, Any]] | list[Suggestion]) -> str:
    result = text
    for suggestion in sorted(suggestions, key=lambda x: x['start'] if isinstance(x, dict) else x.start, reverse=True):
        start = suggestion['start'] if isinstance(suggestion, dict) else suggestion.start
        end = suggestion['end'] if isinstance(suggestion, dict) else suggestion.end
        replacement = suggestion['replacement'] if isinstance(suggestion, dict) else suggestion.replacement
        result = result[:start] + replacement + result[end:]
    return result

def metrics(text: str, count: int) -> dict[str, Any]:
    words = re.findall(r"\b[\w']+\b", text)
    sentences = len(re.findall(r"[.!?]+(?:\s|$)", text)) or (1 if text.strip() else 0)
    avg = round(len(words) / sentences, 1) if sentences else 0
    score = max(0, min(100, round(100 - count * 8 / max(1, len(words) / 28)))) if words else 100
    return {"words": len(words), "characters": len(text), "sentences": sentences,
            "reading_minutes": round(len(words) / 220, 1), "avg_sentence_words": avg, "score": score}

def analyze(text: str) -> dict[str, Any]:
    suggestions = collect(text)
    serialized = [asdict(s) for s in suggestions]
    return {"suggestions": serialized, "corrected": apply_suggestions(text, suggestions),
            "metrics": metrics(text, len(suggestions)), "engine": "Built-in offline checker",
            "notice": "Built-in checks are conservative and do not catch every grammar error. Enable LanguageTool or an ML model for deeper corrections."}

# Optional LanguageTool requires the extra dependency, local Java and model data.
_tool = None

def languagetool_analyze(text: str) -> dict[str, Any]:
    global _tool
    try:
        import language_tool_python
    except ImportError as exc:
        raise RuntimeError("Install optional dependency: pip install -r requirements-language-tool.txt") from exc
    if _tool is None:
        try:
            _tool = language_tool_python.LanguageTool("en-US")
        except Exception as exc:
            raise RuntimeError(f"Could not start local LanguageTool (Java required): {exc}") from exc
    matches = _tool.check(text)
    suggestions = []
    for match in matches:
        if not match.replacements:
            continue
        start, end = match.offset, match.offset + match.error_length
        suggestions.append(Suggestion("", start, end, text[start:end], match.replacements[0], match.message, "Grammar", "medium", "LanguageTool"))
    suggestions.sort(key=lambda s: (s.start, -(s.end-s.start)))
    deduped = []
    for s in suggestions:
        if any(s.start < x.end and x.start < s.end for x in deduped):
            continue
        s.id = f"lt{len(deduped)+1}"
        deduped.append(s)
    return {"suggestions": [asdict(s) for s in deduped], "corrected": apply_suggestions(text, deduped), "metrics": metrics(text, len(deduped)), "engine": "LanguageTool (local)"}
