import difflib

def get_diff_highlighted(original: str, transformed: str):
    """
    original と transformed の文字列を比較して、
    変更点を <mark> でハイライトした HTML を返す
    """
    diff = difflib.ndiff(original.splitlines(), transformed.splitlines())
    result_lines = []
    for line in diff:
        if line.startswith("+ "):
            result_lines.append(f"<mark style='background-color:#d0ffd0;'>{line[2:]}</mark>")
        elif line.startswith("- "):
            result_lines.append(f"<del style='color:red;'>{line[2:]}</del>")
        elif line.startswith("  "):
            result_lines.append(line[2:])
    return "\n".join(result_lines)
