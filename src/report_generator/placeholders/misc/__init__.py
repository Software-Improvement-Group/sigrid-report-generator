import inspect

from . import category_chart, maintainability_galaxy_chart, maintainability_moveable_marker, osh_slide, color_rating

_all_implementations = {
    **category_chart.__dict__,
    **maintainability_galaxy_chart.__dict__,
    **maintainability_moveable_marker.__dict__,
    **osh_slide.__dict__,
    **color_rating.__dict__
}

_placeholders_map = {
    name: obj for name, obj in _all_implementations.items()
    if inspect.isclass(obj) and hasattr(obj, '__placeholder__') and not inspect.isabstract(obj)
}

placeholders = set(_placeholders_map.values())

__all__ = list(_placeholders_map.keys())
