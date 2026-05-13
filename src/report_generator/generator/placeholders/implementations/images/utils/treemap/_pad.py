def parse_pad(pad):
    if isinstance(pad, (int, float)):
        return pad, pad, pad, pad
    if isinstance(pad, tuple) and len(pad) == 2:
        pad_x, pad_y = pad
        return pad_x, pad_x, pad_y, pad_y
    if isinstance(pad, tuple) and len(pad) == 4:
        return pad
    raise ValueError("`pad` can only be a number, or a tuple of two or four numbers.")
