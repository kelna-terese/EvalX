from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Safely retrieves a value from a dictionary using a variable key.
    Used for team-specific submission lookups and slot mapping.
    """
    if dictionary is None:
        return None
    return dictionary.get(key)