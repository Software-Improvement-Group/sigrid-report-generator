# Originally sourced from https://github.com/chenyulue/matplotlib-extra
# Copyright (c) 2022, Chenyu Lue
# Licensed under the MIT License (see LICENSES/MIT-matplotlib-extra.txt)

import re
import textwrap

import matplotlib.artist as artist
import matplotlib.text as mtext
import matplotlib.transforms as trans
from matplotlib.backends.backend_agg import get_hinting_flag
from matplotlib.font_manager import findfont, get_font

from ._padding import resolve_pad

# matplotlib >= 3.11 defaults ``Text._linespacing`` to the string "normal";
# older versions used the numeric multiplier 1.2. AutofitText needs a number to
# compute per-line heights, so fall back to the historical default.
_DEFAULT_LINESPACING = 1.2


class AutofitText(mtext.Text):
    def __repr__(self):
        return f"AutofitText(({self._x}, {self._y}), {self._width}, {self._height}, {self._origin_text})"

    def __init__(
        self,
        xy,
        width,
        height,
        text="",
        *,
        pad=0.0,
        reflow=False,
        grow=False,
        max_fontsize=None,
        min_fontsize=None,
        **kwargs,
    ):
        """Create a `.AutoFitText` instance at *x*, *y* with the string *text*
        autofitting into the box with the size of *width* x *height*.

        Parameters
        ----------
        xy : (float, float)
            The x, y coordinates
        width : float,
            The width of the box, which should be positive.
        height : float
            The height of the box, which should be positive.
        text : str, optional
            The string that needs to be auto-fitted, by default ''
        pad : float, a 2-tuple or a 4-tuple, optional
            The surrounding padding in points from the box edges, by default 0.0. A 2-tuple
            of `(padx, pady)` specifies the horizontal and vertical paddings
            respectively, while a 4-tuple of (`padleft, padright, padtop, padbottom)`
            the padding from the corresponding four edges.
        reflow : bool, optional
            If `True`, then the text will be auto-wrapped to fit into the box, by default False
        grow : bool, optional
            If `True`, then the auto-wrapped text will be as large as possible, by default False.
            This option takes effect only when `wrap = True`.
        max_fontsize : float, optional
            The maximum fontsize in points, by default None. This option makes sure that
            the auto-fitted text won't have a fontsize larger than *max_fontsize*.
        min_fontsize : float, optional
            The minimum fontsize in points, by default None. This option makes sure that
            the auto-fitted text won't have a fontsize smaller than *min_fontsize*.
        **kwargs :
            Additional kwargs are passed to `~matplotlib.text.Text`.
        """
        x, y = xy
        super().__init__(x, y, text, **kwargs)
        self._origin_text = text  # Keep the original, unwrapped text
        self._width = width
        self._height = height
        self._pad = pad
        self._reflow = reflow
        self._grow = grow
        self._max_fontsize = max_fontsize
        self._min_fontsize = min_fontsize
        self._kwargs = kwargs
        self._validate_text()

    def _validate_text(self):
        if self._width < 0 or self._height < 0:
            raise ValueError("`width` and `height` should be a number >= 0.")
        if self._reflow and super().get_rotation():
            raise ValueError(
                "`reflow` option currently only supports the horizontal text object for simplicity."
            )

    @artist.allow_rasterization
    def draw(self, renderer):
        if renderer is not None:
            self._renderer = renderer
        if not self.get_visible():
            return
        if self._origin_text == "" or self._text == "":
            return

        transform = self.get_transform()
        original_txt = self._origin_text
        self._text = original_txt
        dpi = renderer.dpi

        box_size = self._padded_size_in_pixels(renderer, transform)
        adjusted_fontsize = self._base_fontsize(renderer, dpi, box_size)

        if self._reflow:
            adjusted_fontsize = self._reflow_fontsize(
                original_txt, box_size, dpi, adjusted_fontsize
            )

        self._fontproperties.set_size(adjusted_fontsize)

        super().draw(renderer)

    def _padded_size_in_pixels(self, renderer, transform):
        width_in_pixels, height_in_pixels = self._dist2pixels(
            transform, self._width, self._height
        )
        pad_left, pad_right, pad_top, pad_bottom = resolve_pad(self._pad)
        width_in_pixels -= renderer.points_to_pixels(
            pad_left
        ) + renderer.points_to_pixels(pad_right)
        height_in_pixels -= renderer.points_to_pixels(
            pad_top
        ) + renderer.points_to_pixels(pad_bottom)
        return width_in_pixels, height_in_pixels

    def _base_fontsize(self, renderer, dpi, box_size):
        width_in_pixels, height_in_pixels = box_size
        bbox = self.get_window_extent(renderer, dpi=dpi)
        if bbox.width == 0 or bbox.height == 0:
            adjusted_fontsize = 1
        else:
            fontsize = self.get_fontsize()
            adjusted_fontsize = min(
                fontsize * width_in_pixels / bbox.width,
                fontsize * height_in_pixels / bbox.height,
            )
        return self._adjust_fontsize(
            adjusted_fontsize, self._max_fontsize, self._min_fontsize
        )

    def _reflow_fontsize(self, original_txt, box_size, dpi, adjusted_fontsize):
        width_in_pixels, height_in_pixels = box_size
        words = self._split_words(original_txt)
        numeric_linespacing = self._numeric_linespacing()
        fontsizes = [
            self._get_wrapped_fontsize(
                original_txt,
                height_in_pixels,
                width_in_pixels,
                line_num,
                numeric_linespacing,
                dpi,
                self.get_fontproperties(),
            )
            for line_num in range(2, len(words) + 1)
        ]
        if not fontsizes:
            return adjusted_fontsize

        key = (lambda x: x[0]) if self._grow else (lambda x: x[2])
        adjusted_size, wrap_txt, _ = (max if self._grow else min)(fontsizes, key=key)
        adjusted_size = self._adjust_fontsize(
            adjusted_size, self._max_fontsize, self._min_fontsize
        )
        if adjusted_fontsize < adjusted_size:
            self._text = "\n".join(wrap_txt)
            return adjusted_size
        return adjusted_fontsize

    def _get_wrapped_fontsize(self, txt, height, width, n, linespacing, dpi, fontprops):
        words = self._split_words(txt)
        min_length = max(map(len, words))
        wrap_length = max(min_length, len(txt) // n)
        wrap_txt = textwrap.wrap(txt, wrap_length)
        w_fontsize = self._calc_fontsize_from_width(wrap_txt, width, dpi, fontprops)

        h_fontsize = self._calc_fontsize_from_height(
            height, len(wrap_txt), linespacing, dpi
        )

        adjusted_fontsize = min(h_fontsize, w_fontsize)
        delta_w = self._get_line_gap_from_boxedge(
            wrap_txt, adjusted_fontsize, width, dpi, fontprops
        )

        return adjusted_fontsize, wrap_txt, delta_w

    def _get_line_gap_from_boxedge(self, lines, fontsize, width, dpi, fontprops):
        props = fontprops
        font = get_font(findfont(props))
        font.set_size(fontsize, dpi)
        gaps = []
        for line in lines:
            font.set_text(line, 0, flags=get_hinting_flag())
            w, _ = font.get_width_height()
            w = w / 64.0
            gaps.append(abs(w - width))

        return min(gaps)

    def _calc_fontsize_from_width(self, lines, width, dpi, fontprops):
        props = fontprops
        font = get_font(findfont(props))
        font.set_size(props.get_size_in_points(), dpi)
        fontsizes = []
        for line in lines:
            font.set_text(line, 0, flags=get_hinting_flag())
            w, _ = font.get_width_height()
            w = w / 64.0
            adjusted_size = props.get_size_in_points() * width / w
            fontsizes.append(adjusted_size)
        return min(fontsizes)

    def _numeric_linespacing(self):
        ls = self._linespacing
        try:
            return float(ls)
        except (TypeError, ValueError):
            return _DEFAULT_LINESPACING

    def _calc_fontsize_from_height(self, height, n, linespacing, dpi):
        linespacing = float(linespacing)
        h_pixels = height / (n * linespacing - linespacing + 1)
        return self._pixels2points(dpi, h_pixels)

    def _pixels2points(self, dpi, pixels):
        inch_per_point = 1 / 72
        return pixels / dpi / inch_per_point

    def _split_words(self, txt):
        regex = r"[\u4e00-\ufaff]|[0-9]+|[a-zA-Z]+\'*[a-z]*"
        matches = re.findall(regex, txt, re.UNICODE)
        return matches

    def _adjust_fontsize(self, size, max_size, min_size):
        if max_size is not None:
            size = min(max_size, size)
        if min_size is not None:
            size = max(min_size, size)
        return size

    def _dist2pixels(self, transform, width, height):
        box = trans.Bbox([[0, 0], [width, height]])
        _, _, width_in_pixels, height_in_pixels = box.transformed(transform).bounds
        return width_in_pixels, height_in_pixels
