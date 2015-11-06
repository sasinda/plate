# -*- coding:utf-8 -*-

import logging
logger = logging.getLogger('logger')
from common import syntax_highlight


class APIDocument(object):
    """
    Making API Document
    """

    def __init__(self, config):
        """
        Construct of ``APIDocument``

        :param config: ``common.config.Config`` instance.
        :return: ``APIDocument`` instance, ``_g_api_doc``.
        """

        from os.path import join

        self.config = config 
        self.index_file_path = join(self.config.API_DOC_PATH, self.config.API_DOC_INDEX_PATH)
        self.toc = self.read_index(self.index_file_path)
        self.contents = self.create_api_docs()

    def total_reload_docs(self):
        """
        Reload all API Document files.
        """

        logger.info("total_reload_docs")
        self.toc = self.read_index(self.index_file_path)
        self.contents = self.create_api_docs()

    def read_index(self, index_file_path):
        """
        Read API Document index file such as ``index.json``.

        :param index_file_path: index file path
        :return: JSON of index file(``index.json``)
        """
        import json
        from collections import OrderedDict
        return json.load(open(index_file_path), object_pairs_hook=OrderedDict)

    def create_api_docs(self):
        """
        Convert API Document to HTML.
        :return: ``OrderedDict`` instance.
        """
        from os.path import join
        from os.path import split
        from collections import OrderedDict

        docs = OrderedDict()
        for doc_file in self.toc["ORDER"]:

            doc_file = join(self.config.API_DOC_PATH, doc_file)
            from common import conv_md2html
            with open(doc_file, 'r') as f:
                html = conv_md2html(f.read())
                docs[split(doc_file)[1]] = self.modify_html(self.highlight_syntax(self.reordering(html)))

        return docs.values()

    def reordering(self, html):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html)

        up_tags = []
        for up_tag in soup.h1.next_siblings:

            if 'name' in up_tag and up_tag.name in ['pre', 'blockquote']:
                up_tags.append(up_tag)

        up_tags = reversed(up_tags)

        for up_tag in up_tags:
            for prev in up_tag.previous_siblings:
                if prev.name == 'h2':
                    prev.insert_after(up_tag)
                    break
        return soup

    def highlight_syntax(self, soup):
        """
        Highlight code syntax.

        :param soup: bs4 instance
        :return: bs4 instance
        """
        from bs4 import BeautifulSoup
        code_tags = soup.find_all('code')

        for code in code_tags: 
            if code.has_attr('class'):
                lang = code['class']
                code.parent['class'] = "highlight " + lang[0]
                del code['class']
                code.name = "span"

                in_pre_code = syntax_highlight(lang[0], code.string)
                if self.config.CLIPBOARD:
                    s = BeautifulSoup("<blockquote></blockquote>")
                    blockquote = s.blockquote
                    blockquote['class'] = 'highlight ' + lang[0]
                    p = s.new_tag('p')
                    a = s.new_tag('a', href="#")
                    a['class'] = 'clipboard'
                    a["data-clipboard-text"] = code.string
                    a["data-clipboard-action"] = "copy"
                    a.append("copy")
                    p.append(a)
                    blockquote.append(p)

                    in_pre_code += str(blockquote)

                code.parent.replaceWith(in_pre_code)

        return soup

    def modify_html(self, soup):
        """
        Modify HTML

        :param soup: bs4 instance
        :return: HTML
        """
        tags = []
        title_tags = ['h1', 'h2', 'h3', 'h4']
        [tags.extend(soup.find_all(title_tag)) for title_tag in title_tags]

        # h1, h2 add id attribute
        for tag in tags:
            id_str = tag.string.lower()
            splitted = id_str.split(' ')

            if len(splitted) > 0:
                tag['id'] = '-'.join(splitted)

        return soup.prettify(formatter=None)
