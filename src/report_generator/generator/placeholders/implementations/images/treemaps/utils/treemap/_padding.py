def resolve_pad(pad):
    """Expand `pad` into (left, right, top, bottom), shared by _treemap.py and _autofit_text.py."""
    if isinstance(pad, (int, float)):
        return pad, pad, pad, pad
    if isinstance(pad, tuple) and len(pad) == 2:
        pad_left, pad_top = pad
        return pad_left, pad_left, pad_top, pad_top
    if isinstance(pad, tuple) and len(pad) == 4:
        return pad

    raise ValueError("`pad` can only be a number, or a tuple of two or four numbers.")
