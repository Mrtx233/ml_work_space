from collections import deque


from html.parser import HTMLParser

# HTML Parser Module
ALLOWED_TAGS = frozenset([
    'abbr', 'acronym', 'address', 'bdo', 'big', 'blockquote', 'br', 'cite',
    'code', 'dd', 'del', 'dfn', 'dl', 'dt', 'em', 'ins', 'kbd', 'li',
    'listing', 'ol', 'p', 'plaintext', 'pre', 'q', 'samp', 'small', 'strong',
    'sub', 'sup', 'table', 'tbody', 'td', 'th', 'time', 'tr', 'tt', 'ul', 'var'
])
REPLACE_TAGS = {
    'b': 'strong', 'h1': 'strong', 'h2': 'strong', 'h3': 'strong',
    'h4': 'strong', 'h5': 'strong', 'h6': 'strong', 'i': 'em'
}
PURGE_TAGS = ('script', 'img', 'input', 'style')
ALLOWED_ATTRS = frozenset([
    'height', 'width', 'colspan', 'cellspacing', 'callpadding', 'border',
    'bgcolor', 'alt', 'align', 'valign', 'dir', 'headers', 'reversed',
    'rows', 'rowspan', 'scope', 'span', 'start', 'summary', 'title', 'value'
])


class AllowAll(object):
    def __contains__(self, value):
        return True


class SafeHtmlParser(HTMLParser):
    def __init__(self, allowed_tags=ALLOWED_TAGS, replace_tags=REPLACE_TAGS,
                 tags_to_purge=PURGE_TAGS, allowed_attrs=ALLOWED_ATTRS):
        self.reset()
        self._body = []
        self.skip = False
        self._unclosed = deque()
        if allowed_tags is None:
            allowed_tags = AllowAll()
        if allowed_attrs is None:
            allowed_attrs = AllowAll()
        self.allowed_tags = allowed_tags
        self.replace_tags = replace_tags
        self.tags_to_purge = tags_to_purge
        self.allowed_attrs = allowed_attrs
        super(SafeHtmlParser, self).__init__()

    def feed(self, data):
        self._body, self._unclosed, self.skip = [], deque(), False
        self.rawdata = self.rawdata + data
        self.goahead(0)
        self._close_remaining_tags()
        return ''.join(self._body).strip()

    def handle_starttag(self, tag, attrs):
        self._handle_open(tag, attrs)
        self._unclosed.appendleft(tag)

    def handle_startendtag(self, tag, attrs):
        self._handle_open(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        tag = tag.lower()
        try:
            last_opened = self._unclosed.popleft()
            while last_opened != tag:
                self._body.append(self._build_close_tag(last_opened))
                last_opened = self._unclosed.popleft()
        except IndexError:
            return
        if self.skip and tag in self.tags_to_purge:
            self.skip = False
            return
        if tag not in self.allowed_tags and tag not in self.replace_tags:
            return
        self._body.append(self._build_close_tag(tag))

    def handle_data(self, data):
        if self.skip:
            return
        self._body.append(data)

    def handle_entityref(self, name):
        self._body.append('&{};'.format(name))

    def _handle_open(self, tag, attrs, closed=False):
        tag = tag.lower()
        if tag in self.tags_to_purge:
            if not closed:
                self.skip = True
            return
        if tag not in self.allowed_tags and tag not in self.replace_tags:
            return
        self._body.append(self._build_open_tag(tag, attrs))

    def _build_open_tag(self, tag, attrs):
        tag = self.replace_tags.get(tag, tag)
        attrs = [(k, v) for k, v in attrs if k.lower() in self.allowed_attrs]
        return '<{tag}{has_attrs}{attrs}>'.format(
            tag=tag, has_attrs=' ' * bool(attrs),
            attrs=(' '.join('{}="{}"'.format(*a) for a in attrs) if attrs else ''))

    def _build_close_tag(self, tag):
        tag = self.replace_tags.get(tag, tag)
        return '</{}>'.format(tag)

    def _close_remaining_tags(self):
        for tag in self._unclosed:
            self._body.append(self._build_close_tag(tag))
