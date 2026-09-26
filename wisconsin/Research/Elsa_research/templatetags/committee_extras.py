from django import template

register = template.Library()


@register.filter
def dictkey(d, key):
    if d is None:
        return None
    return d.get(key)
