# Originally sourced from https://github.com/chenyulue/matplotlib-extra
# Copyright (c) 2022, Chenyu Lue
# Licensed under the MIT License (see LICENSES/MIT-matplotlib-extra.txt)

import re
import textwrap
from dataclasses import dataclass

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


@dataclass(frozen=True)
class FitOptions:
    """How an `AutofitText` fits its text into the box.

    pad : float, a 2-tuple or a 4-tuple
        The surrounding padding in points from the box edges. A 2-tuple of
        `(padx, pady)` specifies the horizontal and vertical paddings
        respectively, while a 4-tuple of (`padleft, padright, padtop, padbottom)`
        the padding from the corresponding four edges.
    reflow : bool
        If `True`, then the text will be auto-wrapped, as large as possible, to fit into the box.
    max_fontsize : float, optional
        The auto-fitted text won't have a fontsize larger than this.
    min_fontsize : float, optional
        The auto-fitted text won't have a fontsize smaller than this.
    """

    pad: float | tuple = 0.0
    reflow: bool = False
    max_fontsize: float | None = None
    min_fontsize: float | None = None


@dataclass(frozen=True)
class _Measure:
    """What is needed to measure text in pixels: resolution, font and line spacing."""

    dpi: float
    fontprops: object
    linespacing: float


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
        fit=FitOptions(),
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
        fit : FitOptions, optional
            Padding, reflow and fontsize limits, by default no padding and no reflow.
        **kwargs :
            Additional kwargs are passed to `~matplotlib.text.Text`.
        """
        x, y = xy
        super().__init__(x, y, text, **kwargs)
        self._origin_text = text  # Keep the original, unwrapped text
        self._width = width
        self._height = height
        self._fit = fit
        self._kwargs = kwargs
        self._validate_text()

    def _validate_text(self):
        if self._width < 0 or self._height < 0:
            raise ValueError("`width` and `height` should be a number >= 0.")
        if self._fit.reflow and super().get_rotation():
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

        if self._fit.reflow:
            adjusted_fontsize = self._reflow_fontsize(
                original_txt, box_size, self._measure(dpi), adjusted_fontsize
            )

        self._fontproperties.set_size(adjusted_fontsize)

        super().draw(renderer)

    def _padded_size_in_pixels(self, renderer, transform):
        width_in_pixels, height_in_pixels = self._dist2pixels(
            transform, self._width, self._height
        )
        pad_left, pad_right, pad_top, pad_bottom = resolve_pad(self._fit.pad)
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
        return self._adjust_fontsize(adjusted_fontsize)

    def _measure(self, dpi):
        return _Measure(
            dpi=dpi,
            fontprops=self.get_fontproperties(),
            linespacing=self._numeric_linespacing(),
        )

    def _reflow_fontsize(self, original_txt, box_size, measure, adjusted_fontsize):
        words = self._split_words(original_txt)
        fontsizes = [
            self._get_wrapped_fontsize(original_txt, box_size, line_num, measure)
            for line_num in range(2, len(words) + 1)
        ]
        if not fontsizes:
            return adjusted_fontsize

        adjusted_size, wrap_txt = max(fontsizes, key=lambda fit: fit[0])
        adjusted_size = self._adjust_fontsize(adjusted_size)
        if adjusted_fontsize < adjusted_size:
            self._text = "\n".join(wrap_txt)
            return adjusted_size
        return adjusted_fontsize

    def _get_wrapped_fontsize(self, txt, box_size, n, measure):
        width, height = box_size
        words = self._split_words(txt)
        min_length = max(map(len, words))
        wrap_length = max(min_length, len(txt) // n)
        wrap_txt = textwrap.wrap(txt, wrap_length)
        w_fontsize = self._calc_fontsize_from_width(wrap_txt, width, measure)

        h_fontsize = self._calc_fontsize_from_height(height, len(wrap_txt), measure)

        return min(h_fontsize, w_fontsize), wrap_txt

    def _calc_fontsize_from_width(self, lines, width, measure):
        props = measure.fontprops
        font = get_font(findfont(props))
        font.set_size(props.get_size_in_points(), measure.dpi)
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

    def _calc_fontsize_from_height(self, height, n, measure):
        linespacing = measure.linespacing
        h_pixels = height / (n * linespacing - linespacing + 1)
        return self._pixels2points(measure.dpi, h_pixels)

    def _pixels2points(self, dpi, pixels):
        inch_per_point = 1 / 72
        return pixels / dpi / inch_per_point

    def _split_words(self, txt):
        regex = r"[\u4e00-\ufaff]|[0-9]+|[a-zA-Z]+\'*[a-z]*"
        matches = re.findall(regex, txt, re.UNICODE)
        return matches

    def _adjust_fontsize(self, size):
        if self._fit.max_fontsize is not None:
            size = min(self._fit.max_fontsize, size)
        if self._fit.min_fontsize is not None:
            size = max(self._fit.min_fontsize, size)
        return size

    def _dist2pixels(self, transform, width, height):
        box = trans.Bbox([[0, 0], [width, height]])
        _, _, width_in_pixels, height_in_pixels = box.transformed(transform).bounds
        return width_in_pixels, height_in_pixels
