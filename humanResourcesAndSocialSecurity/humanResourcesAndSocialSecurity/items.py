from __future__ import absolute_import

import scrapy
from collections import defaultdict
from itemloaders.processors import Join, MapCompose, Identity
from w3lib.html import remove_tags
from .utils.processors import Text, Number, Price, Date, Url, Image, SafeHtml


class PortiaItem(scrapy.Item):
    fields = defaultdict(
        lambda: scrapy.Field(
            input_processor=Identity(),
            output_processor=Identity()
        )
    )

    def __setitem__(self, key, value):
        self._values[key] = value

    def __repr__(self):
        data = str(self)
        if not data:
            return '%s' % self.__class__.__name__
        return '%s(%s)' % (self.__class__.__name__, data)

    def __str__(self):
        if not self._values:
            return ''
        string = super(PortiaItem, self).__repr__()
        return string


class AgriItem(PortiaItem):
    publish_time = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    title = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    content = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    menu = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    issuer = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    fileno = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    indexnumber = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    writtendate = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    category = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    status = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )

    source = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    attachment = scrapy.Field(
        input_processor=Url(),
        output_processor=Identity(),
    )
    author = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    tags = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )


class ListItems(PortiaItem):
    detail_urls = scrapy.Field(
        input_processor=Text(),
        output_processor=Identity(),
    )
    publish_times = scrapy.Field(
        input_processor=Text(),
        output_processor=Identity(),
    )
    next_page = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
    total_page = scrapy.Field(
        input_processor=Text(),
        output_processor=Join(),
    )
