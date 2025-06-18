from markupsafe import Markup

def nl2br(value):
    """改行を<br>タグに変換するJinja2フィルター"""
    if not value:
        return ''
    return Markup(value.replace('\n', '<br>')) 