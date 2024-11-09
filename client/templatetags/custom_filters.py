from django import template
import logging
register = template.Library()

logger = logging.getLogger('django')

@register.filter(name='get_item')
def get_item(dc, key):
    return dc.get(key)

@register.filter(name='split')
def split(objs):
    return objs.split(',')
