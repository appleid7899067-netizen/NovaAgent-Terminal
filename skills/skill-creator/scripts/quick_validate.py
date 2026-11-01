#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version

Usage:
    quick_validate.py <skill-name>
    quick_validate.py <absolute-path-to-skill>
    quick_validate.py --path <absolute-path-to-skill>

Examples:
    quick_validate.py my-skill
    quick_validate.py /home/ubuntu/skills/my-skill
    quick_validate.py --path "/absolute/path/to/skills/my-skill"

Skill names resolve under /home/ubuntu/skills/ on cloud runtimes, or under the
Manus user skill directory beside the installed skill-creator on Work Locally.

Frontmatter is parsed with PyYAML when it is installed. Without PyYAML, a built-in
parser handles the usual frontmatter forms and asks for PyYAML for anything else.
"""

import argparse
import sys
import re
from datetime import date
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

SKILLS_BASE_PATH = Path("/home/ubuntu/skills")
# Work Locally keeps the managed official copy in <data>/skills and the user's
# Manus skills in <data>/user-skills (manus-cli UserSkillsDirForHome).
USER_SKILLS_PATH = Path(__file__).resolve().parents[2].parent / "user-skills"


def default_skills_root():
    """Return the cloud skill root, else the Work Locally user skill root, else None."""
    for root in (SKILLS_BASE_PATH, USER_SKILLS_PATH):
        if root.is_dir():
            return root
    return None


def skill_name_error(name):
    """Return why a skill name is invalid, or None for a valid hyphen-case name."""
    # Check naming convention (hyphen-case: lowercase with hyphens)
    if not re.match(r'^[a-z0-9-]+$', name):
        return f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)"
    if name.startswith('-') or name.endswith('-') or '--' in name:
        return f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
    # Check name length (max 64 characters per spec)
    if len(name) > 64:
        return f"Name is too long ({len(name)} characters). Maximum is 64 characters."
    return None


def resolve_skill_path(skill_path_or_name):
    """
    Resolve skill path to absolute path.

    If given an absolute path, use it directly.
    If given a skill name or relative path, resolve it under the default skill root.
    """
    path = Path(skill_path_or_name)

    # If it's an absolute path, use it directly
    if path.is_absolute():
        return path

    # Otherwise, treat it as a skill name and look in the default skill root
    return (default_skills_root() or SKILLS_BASE_PATH) / skill_path_or_name


class _NeedsPyYAML(Exception):
    """Frontmatter uses YAML outside the built-in parser's subset."""


# The built-in parser agrees with PyYAML wherever it returns a result: it raises
# ValueError where PyYAML reports invalid YAML and _NeedsPyYAML for anything else.
_KEY_LINE = re.compile(r'([A-Za-z0-9_-]+):(?: +(.*))?')
_NON_PRINTABLE = re.compile('[^\x09\x0a\x0d\x20-\x7e\x85\xa0-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]')
_PLAIN_STOP = re.compile(r':(?: |$)| #')
_COMMENT_TAIL = re.compile(r'(?: +#.*)?')
_BLOCK_HEADER = re.compile(r'([|>])([+-]?)(?: +#.*)?')
_ESCAPES = {'0': '\0', 'a': '\a', 'b': '\b', 't': '\t', 'n': '\n', 'v': '\v', 'f': '\f', 'r': '\r', 'e': '\x1b',
            ' ': ' ', '"': '"', '/': '/', '\\': '\\', 'N': '\x85', '_': '\xa0', 'L': '\u2028', 'P': '\u2029'}
_HEX_ESCAPES = {'x': 2, 'u': 4, 'U': 8}
# PyYAML's implicit resolvers for plain scalars, in its resolution order.
_IMPLICIT_TYPES = [(kind, re.compile(pattern, re.X)) for kind, pattern in (
    ('bool', r'^(?:yes|Yes|YES|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)$'),
    ('float', r'''^(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?
                |\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?
                |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*
                |[-+]?\.(?:inf|Inf|INF)
                |\.(?:nan|NaN|NAN))$'''),
    ('int', r'''^(?:[-+]?0b[0-1_]+
                |[-+]?0[0-7_]+
                |[-+]?(?:0|[1-9][0-9_]*)
                |[-+]?0x[0-9a-fA-F_]+
                |[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$'''),
    ('merge', r'^(?:<<)$'),
    ('null', r'^(?: ~ |null|Null|NULL | )$'),
    ('timestamp', r'''^(?:[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]
                |[0-9][0-9][0-9][0-9] -[0-9][0-9]? -[0-9][0-9]?
                 (?:[Tt]|[ \t]+)[0-9][0-9]?
                 :[0-9][0-9] :[0-9][0-9] (?:\.[0-9]*)?
                 (?:[ \t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?)$'''),
    ('value', r'^(?:=)$'),
)]


def _typed_plain(text):
    """Type a plain scalar like PyYAML; non-string results are placeholders of the right type."""
    for kind, pattern in _IMPLICIT_TYPES:
        if pattern.match(text):
            if kind in ('merge', 'value') or kind == 'timestamp' and len(text) != 10:
                raise _NeedsPyYAML
            if kind == 'timestamp':
                return date(*map(int, text.split('-')))
            return {'bool': text.lower() in ('yes', 'true', 'on'), 'float': 0.0, 'int': 0, 'null': None}[kind]
    return text


def _has_content(lines):
    """Return whether lines hold anything besides blanks and comments."""
    return any(line.strip(' ') and not line.lstrip(' ').startswith('#') for line in lines)


def _quoted(text):
    """Return the single-line quoted scalar at the start of text and the text after it."""
    quote, chars, index = text[0], [], 1
    while index < len(text):
        char = text[index]
        if char == quote == "'" and text[index + 1:index + 2] == "'":
            chars.append("'")
            index += 2
        elif char == quote:
            return ''.join(chars), text[index + 1:]
        elif char == '\\' and quote == '"':
            code = text[index + 1:index + 2]
            width = _HEX_ESCAPES.get(code, 0)
            digits = text[index + 2:index + 2 + width]
            if code in _ESCAPES:
                chars.append(_ESCAPES[code])
            elif width and re.fullmatch('[0-9A-Fa-f]{%d}' % width, digits):
                chars.append(chr(int(digits, 16)))
            elif not code:
                raise _NeedsPyYAML  # an escaped line break continues the scalar
            else:
                raise ValueError(f"invalid escape sequence '\\{code}{digits}'")
            index += 2 + width
        else:
            chars.append(char)
            index += 1
    raise _NeedsPyYAML  # the scalar continues on the next line


def _fold_plain(first, block):
    """Fold a plain scalar and its continuation lines the way PyYAML does."""
    value, breaks, ended = None, 0, False
    for line in [first, *block]:
        text = line.strip(' ')
        if not text:
            breaks += 1
        elif ended or text.startswith('#'):
            if not text.startswith('#'):
                raise _NeedsPyYAML  # content after a comment
            ended = True
        else:
            stop = _PLAIN_STOP.search(text)
            if stop and stop.group().startswith(':'):
                raise ValueError("mapping values are not allowed here")
            if stop:
                text, ended = text[:stop.start()].rstrip(' '), True
            value = text if value is None else value + ('\n' * breaks if breaks else ' ') + text
            breaks = 0
    return value


def _inline(text, block=()):
    """Parse a value written on its key's line, with any plain continuation lines below it."""
    if not text or text.startswith('#'):
        return None
    if text[0] in '"\'':
        value, rest = _quoted(text)
        if not _COMMENT_TAIL.fullmatch(rest) or _has_content(block):
            raise _NeedsPyYAML
        return value
    if text[0] in '`@%,':
        raise ValueError(f"found character '{text[0]}' that cannot start any token")
    if text[0] in '|>[]{}&*!' or text[:2] in ('- ', '? ', ': ') or text in ('-', '?', ':'):
        raise _NeedsPyYAML
    return _typed_plain(_fold_plain(text, block))


def _block_scalar(header, block, at_end):
    """Parse a literal (|) or folded (>) block scalar with automatic indentation."""
    match = _BLOCK_HEADER.fullmatch(header)
    if not match:
        raise _NeedsPyYAML
    style, chomping = match.groups()
    content = [index for index, line in enumerate(block) if line.strip(' ')]
    if not content:
        return '\n' * (len(block) - (1 if at_end and block else 0)) if chomping == '+' else ''
    last = content[-1]
    indent = len(block[content[0]]) - len(block[content[0]].lstrip(' '))
    for line in block:
        if not line.strip(' ') and len(line) > indent:
            raise _NeedsPyYAML  # spaces beyond the indentation are content
        if line.strip(' ') and (len(line) - len(line.lstrip(' ')) < indent or style == '>' and line[indent] == ' '):
            raise _NeedsPyYAML  # dedented lines and more-indented folded lines
    lines = [line[indent:] for line in block[:last + 1]]
    if style == '|':
        value = '\n'.join(lines)
    else:
        parts, breaks = [], 0
        for text in lines:
            if not text:
                breaks += 1
                continue
            parts.append(('\n' * breaks if breaks or not parts else ' ') + text)
            breaks = 0
        value = ''.join(parts)
    line_break = '\n' if last < len(block) - 1 or not at_end else ''
    trailing = len(block) - 1 - last - (1 if at_end else 0)
    if chomping == '-':
        return value
    return value + line_break + ('\n' * max(trailing, 0) if chomping == '+' else '')


def _nested(block):
    """Parse a one-level mapping or sequence of inline values, or None when there is none."""
    entries = [line for line in block if _has_content([line])]
    if not entries:
        return None
    indent = len(entries[0]) - len(entries[0].lstrip(' '))
    if any(len(line) - len(line.lstrip(' ')) != indent for line in entries):
        raise _NeedsPyYAML
    items = [line[indent:] for line in entries]
    if all(item.startswith('- ') for item in items):
        values = [item[2:].strip(' ') for item in items]
        if any(re.search(r':(?: |$)', value) for value in values):
            raise _NeedsPyYAML  # a sequence entry may hold a mapping
        return [_inline(value) for value in values]
    matches = [_KEY_LINE.fullmatch(item) for item in items]
    if not all(matches):
        raise _NeedsPyYAML
    mapping = {}
    for match in matches:
        key = match.group(1)
        if _typed_plain(key) != key:
            raise _NeedsPyYAML
        if key in mapping:
            raise ValueError(f"duplicate key '{key}'")
        mapping[key] = _inline((match.group(2) or '').rstrip(' '))
    return mapping


def _parse_frontmatter(text):
    """Parse frontmatter without PyYAML, covering top-level keys and one nested level."""
    if _NON_PRINTABLE.search(text):
        raise ValueError("special characters are not allowed")
    if any(char in text for char in '\t\r\x85\u2028\u2029'):
        raise _NeedsPyYAML
    lines = text.split('\n')
    data, index = {}, 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not _has_content([line]):
            continue
        match = _KEY_LINE.fullmatch(line)
        if not match or _typed_plain(match.group(1)) != match.group(1):
            raise _NeedsPyYAML
        start = index
        while index < len(lines) and lines[index][:1] in ('', ' '):
            index += 1
        key, inline, block = match.group(1), (match.group(2) or '').rstrip(' '), lines[start:index]
        if key in data:
            raise ValueError(f"duplicate key '{key}'")
        if not inline or inline.startswith('#'):
            data[key] = _nested(block)
        elif inline[0] in '|>':
            data[key] = _block_scalar(inline, block, index == len(lines))
        else:
            data[key] = _inline(inline, block)
    return data or None


def _duplicate_key(node):
    """Return a key repeated in a composed top-level mapping or a mapping directly under it."""
    if not isinstance(node, yaml.MappingNode):
        return None
    for mapping in [node, *(value for _, value in node.value if isinstance(value, yaml.MappingNode))]:
        keys = [key.value for key, _ in mapping.value if isinstance(key, yaml.ScalarNode)]
        for index, key in enumerate(keys):
            if key in keys[:index]:
                return key
    return None


def _load_frontmatter(text):
    """Load frontmatter with PyYAML when installed, else with the built-in parser."""
    if yaml is None:
        return _parse_frontmatter(text)
    try:
        data = yaml.safe_load(text)
        duplicate = _duplicate_key(yaml.compose(text, Loader=yaml.SafeLoader))
    except (yaml.YAMLError, ValueError) as error:
        raise ValueError(str(error)) from error
    # Node's skill loader rejects repeated keys, so PyYAML's last-wins result is not enough.
    if duplicate is not None:
        raise ValueError(f"duplicate key '{duplicate}'")
    return data


def validate_skill(skill_path_or_name):
    """Basic validation of a skill"""
    skill_path = resolve_skill_path(skill_path_or_name)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    try:
        content = skill_md.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        return False, f"Cannot read SKILL.md: {error}"
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = _load_frontmatter(frontmatter_text)
    except _NeedsPyYAML:
        return False, "PyYAML is required to check this frontmatter; install it in a task-local virtual environment and retry."
    except ValueError as e:
        return False, f"Invalid YAML in frontmatter: {e}"
    if not isinstance(frontmatter, dict):
        return False, "Frontmatter must be a YAML dictionary"

    # Define allowed properties
    ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata'}

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(map(str, unexpected_keys)))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if not name:
        return False, "Name cannot be empty"
    name_error = skill_name_error(name)
    if name_error:
        return False, name_error

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if not description:
        return False, "Description cannot be empty"
    if description.startswith('[TODO'):
        return False, "Description still has the template placeholder; describe what the skill does and when to use it"
    # Check for angle brackets
    if '<' in description or '>' in description:
        return False, "Description cannot contain angle brackets (< or >)"
    # Check description length (max 1024 characters per spec)
    if len(description) > 1024:
        return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    return True, "Skill is valid!"

def main():
    parser = argparse.ArgumentParser(
        description="Validate a skill at an explicit path or by its legacy cloud name."
    )
    parser.add_argument(
        "skill_name",
        nargs="?",
        help="Skill name in the default skill root, or an absolute skill path",
    )
    parser.add_argument(
        "--path",
        metavar="DIRECTORY",
        help="Explicit skill directory, recommended for Work Locally",
    )
    args = parser.parse_args()

    if bool(args.skill_name) == bool(args.path):
        parser.error("provide exactly one skill name/path or --path DIRECTORY")

    skill_input = str(Path(args.path).expanduser().resolve()) if args.path else args.skill_name
    resolved_path = resolve_skill_path(skill_input)

    print(f"Validating skill at: {resolved_path}")

    valid, message = validate_skill(skill_input)
    print(message)
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
