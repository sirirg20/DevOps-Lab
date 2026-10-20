"""A tiny YAML reader for the plain subset the manifests in k8s/ use.

Supported: block mappings, block sequences (of scalars or mappings), scalars
(strings, quoted strings, ints, booleans), "---" document separators and "#"
comment lines. Not supported on purpose: anchors, flow style ({} and [] with
content), multi-line scalars, tags. It exists because PyYAML is not installed
here; it raises ValueError on anything outside the subset instead of guessing.
"""
import re


def load_all(text):
    """Return a list of documents (dicts), one per "---" separated section."""
    docs = []
    for chunk in re.split(r"(?m)^---\s*$", text):
        lines = []
        for raw in chunk.splitlines():
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            if "\t" in raw:
                raise ValueError(f"tab character in line: {raw!r}")
            lines.append((len(raw) - len(raw.lstrip(" ")), raw.strip()))
        if lines:
            value, pos = _block(lines, 0, lines[0][0])
            if pos != len(lines):
                raise ValueError(f"unparsed content near: {lines[pos][1]!r}")
            docs.append(value)
    return docs


def _scalar(token):
    token = token.strip()
    if token.startswith(('"', "'")):
        if len(token) < 2 or token[-1] != token[0]:
            raise ValueError(f"unterminated quoted string: {token!r}")
        return token[1:-1]
    if re.search(r"\s#", token):
        raise ValueError(f"inline comments are not supported: {token!r}")
    if token[:1] in "{[&*!|>" and token not in ("[]", "{}"):
        raise ValueError(f"unsupported YAML syntax: {token!r}")
    if token == "[]":
        return []
    if token == "{}":
        return {}
    if token in ("true", "false"):
        return token == "true"
    if re.fullmatch(r"-?\d+", token):
        return int(token)
    return token


def _split_key(content):
    """Split 'key: value' / 'key:' ; returns (key, rest) or None for a plain scalar."""
    match = re.match(r'^([^\s:"\'][^:]*?|"[^"]*"|\'[^\']*\'):(?:\s+(.*))?$', content)
    if not match:
        return None
    return match.group(1).strip("\"'"), (match.group(2) or "")


def _block(lines, pos, indent):
    content = lines[pos][1]
    if content.startswith("- ") or content == "-":
        return _sequence(lines, pos, indent)
    return _mapping(lines, pos, indent)


def _mapping(lines, pos, indent):
    result = {}
    while pos < len(lines):
        cur_indent, content = lines[pos]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise ValueError(f"unexpected indentation at: {content!r}")
        if content.startswith("- "):
            break
        split = _split_key(content)
        if split is None:
            raise ValueError(f"expected 'key: value', got: {content!r}")
        key, rest = split
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        pos += 1
        if rest:
            result[key] = _scalar(rest)
        elif pos < len(lines) and (lines[pos][0] > indent or
                                   (lines[pos][0] == indent and lines[pos][1].startswith("- "))):
            result[key], pos = _block(lines, pos, lines[pos][0])
        else:
            result[key] = None
    return result, pos


def _sequence(lines, pos, indent):
    result = []
    while pos < len(lines):
        cur_indent, content = lines[pos]
        if cur_indent != indent or not (content.startswith("- ") or content == "-"):
            break
        rest = content[2:].strip() if content != "-" else ""
        if not rest:
            pos += 1
            item, pos = _block(lines, pos, lines[pos][0])
            result.append(item)
        elif _split_key(rest) is not None:
            # "- key: value": re-read the dash line as a mapping line two columns deeper.
            lines[pos] = (indent + 2, rest)
            item, pos = _mapping(lines, pos, indent + 2)
            result.append(item)
        else:
            result.append(_scalar(rest))
            pos += 1
    return result, pos
