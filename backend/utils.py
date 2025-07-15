# backend/utils.py
import markupsafe
import markdown

# --- CUSTOM JINJA FILTERS ---

def nl2br(value):
    if value is None:
        return ''
    return markupsafe.Markup(markupsafe.escape(value).replace('\n', '<br>\n'))

def markdown_to_html_filter(value):
    if value is None:
        return ''
    return markupsafe.Markup(markdown.markdown(value, extensions=['fenced_code', 'tables']))

def truncate_filter(s, length=100, end='...'):
    if s is None:
        return ''
    s = str(s)
    if len(s) > length:
        return s[:length] + end
    else:
        return s