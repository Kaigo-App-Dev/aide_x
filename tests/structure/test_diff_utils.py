import pytest
from src.structure.diff_utils import generate_diff_html

def test_diff_html_addition():
    before = {"a": 1}
    after = {"a": 1, "b": 2}
    html = generate_diff_html(before, after)
    assert '追加された項目' in html
    assert 'b' in html
    assert '2' in html

def test_diff_html_removal():
    before = {"a": 1, "b": 2}
    after = {"a": 1}
    html = generate_diff_html(before, after)
    assert '削除された項目' in html
    assert 'b' in html
    assert '2' in html

def test_diff_html_change():
    before = {"a": 1, "b": 2}
    after = {"a": 1, "b": 3}
    html = generate_diff_html(before, after)
    assert '変更された項目' in html
    assert 'b' in html
    assert '旧' in html and '新' in html
    assert '2' in html and '3' in html

def test_diff_html_nested():
    before = {"a": {"x": 1, "y": 2}}
    after = {"a": {"x": 1, "y": 3}}
    html = generate_diff_html(before, after)
    assert '変更された項目' in html
    assert 'a' in html and 'y' in html
    assert '2' in html and '3' in html

def test_diff_html_no_change():
    before = {"a": 1}
    after = {"a": 1}
    html = generate_diff_html(before, after)
    assert '変更なし' in html

def test_diff_html_list_change():
    before = {"a": [1, 2, 3]}
    after = {"a": [1, 2, 4]}
    html = generate_diff_html(before, after)
    # DeepDiffはリストの差分もpathで出す
    assert '変更された項目' in html or 'diff-section' in html
    assert 'a' in html
 