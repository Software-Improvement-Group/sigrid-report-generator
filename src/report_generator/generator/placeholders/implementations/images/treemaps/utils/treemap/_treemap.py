# Originally sourced from https://github.com/chenyulue/matplotlib-extra
# Copyright (c) 2022, Chenyu Lue
# Licensed under the MIT License (see LICENSES/MIT-matplotlib-extra.txt)
#
# Modifications from the original:
# - Replaced deprecated cm.get_cmap() with matplotlib.colormaps (Matplotlib 3.9+)
# - Fixed pandas Copy-on-Write violations (pandas 2.0+)
# - Grouped style keyword arguments into TreemapStyle and split draw_subgroup()/
#   get_plot_data() into focused helpers (maintainability)
# - Trimmed the general-purpose API (padded/"split" layout, non-DataFrame inputs,
#   the discarded TreemapContainer return value, arbitrary axis normalization,
#   uncommon position codes) down to what this codebase's one caller uses
#   (maintainability)

import itertools
from dataclasses import dataclass, field

import matplotlib
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.transforms as trans
import numpy as np
import pandas as pd
import squarify

from . import _autofit_text as _at
from ._padding import resolve_pad

_TEXTPROPS_LAYOUT_KEYS = (
    "grow",
    "reflow",
    "xmax",
    "ymax",
    "place",
    "max_fontsize",
    "min_fontsize",
    "padx",
    "pady",
)

# Axes are always normalized to a 0-100 square, top-anchored (row 0 at the top).
_NORM_SIZE = 100
_DEFAULT_PAD = 0.0


@dataclass(frozen=True)
class TreemapStyle:
    """Tile/label styling, coloring, and padding for a treemap's leaf and subgroup levels."""

    cmap: object = None
    rectprops: dict = field(default_factory=dict)
    textprops: dict = field(default_factory=dict)
    subgroup_rectprops: dict = field(default_factory=dict)
    subgroup_textprops: dict = field(default_factory=dict)


@dataclass(frozen=True)
class _SubgroupDrawContext:
    """Per-call context shared by the rect/text drawing helpers in draw_subgroup()."""

    axes: object
    cmap: object
    rectprops: dict
    textprops: dict
    is_leaf: bool


@dataclass(frozen=True)
class _ColorResolution:
    """Colors resolved once per subgroup and reused for every row it contains."""

    colors: object
    fill_is_numeric: bool
    norm: object


@dataclass(frozen=True)
class _RectDraw:
    """The rectangle patch drawn for one row, and its lower-left y in axes coordinates."""

    patch: object
    y0: float


@dataclass(frozen=True)
class PlotColumns:
    """Column selectors that shape get_plot_data()'s output DataFrame."""

    area: object = None
    labels: object = None
    fill: object = None
    levels: object = None


@dataclass(frozen=True)
class _OptionalColumnSpec:
    """Destination column name and the argument name used in get_plot_data() error messages."""

    colname: str
    arg_name: str


def treemap(axes, data, *, columns=None, style=None):
    """Plot a treemap based on the `squarify` package.

    Parameters
    ----------
    axes : Axes
        The axes where the treemap will be drawn.
    data : DataFrame
        The data to plot.
    columns : PlotColumns, optional
        Column selectors (area/labels/fill/levels) for `data`, by default `PlotColumns()`.
    style : TreemapStyle, optional
        Tile/label styling, coloring, and padding, by default `TreemapStyle()`.
    """
    columns = columns or PlotColumns()
    style = style or TreemapStyle()

    plot_data = get_plot_data(data, columns)
    subgroups = get_subgroups(plot_data, columns.levels)
    squarified = _squarify_treemap_subgroups(subgroups, columns.levels, style)

    axes.set_xlim([0, _NORM_SIZE])
    axes.set_ylim([0, _NORM_SIZE])

    for key, subgroup in squarified.items():
        context = _resolve_subgroup_draw_context(axes, key, columns.levels, style)
        if context is not None:
            draw_subgroup(subgroup, context)


def _squarify_treemap_subgroups(subgroups, levels, style):
    sub_pads = {levels[-1]: style.rectprops.get("pad", _DEFAULT_PAD)}
    for k, v in style.subgroup_rectprops.items():
        sub_pads[k] = v.get("pad", _DEFAULT_PAD)
    return squarify_subgroups(subgroups, levels, sub_pads)


def _resolve_subgroup_draw_context(axes, key, levels, style):
    """Build the _SubgroupDrawContext for one subgroup key, or None if it should be skipped."""
    if key in style.subgroup_rectprops:
        rectprops = style.subgroup_rectprops[key]
        textprops = style.subgroup_textprops.get(key, {})
        is_leaf = False
    elif key == levels[-1] or key not in levels:
        rectprops = style.rectprops
        textprops = style.textprops
        is_leaf = True
    else:
        return None

    return _SubgroupDrawContext(
        axes=axes,
        cmap=style.cmap,
        rectprops=rectprops,
        textprops=textprops,
        is_leaf=is_leaf,
    )


def draw_subgroup(subgroup, context):
    color_res = _resolve_subgroup_colors(subgroup, context.cmap)

    for idx in subgroup.index:
        rect_draw = _draw_subgroup_rect(subgroup, idx, context, color_res)

        if context.textprops and ("_label_" in subgroup.columns):
            _draw_subgroup_text(subgroup, idx, context, rect_draw)


def _resolve_subgroup_colors(subgroup, cmap):
    if "_fill_" not in subgroup.columns:
        return _ColorResolution(colors=None, fill_is_numeric=False, norm=None)

    colors = get_colormap(cmap, subgroup["_fill_"])
    fill_is_numeric = pd.api.types.is_numeric_dtype(subgroup.loc[:, "_fill_"].dtype)
    norm = None
    if fill_is_numeric:
        max_value = subgroup["_fill_"].max()
        min_value = subgroup["_fill_"].min()
        norm = mcolors.Normalize(vmin=min_value, vmax=max_value)
    return _ColorResolution(colors=colors, fill_is_numeric=fill_is_numeric, norm=norm)


def _draw_subgroup_rect(subgroup, idx, context, color_res):
    rectprops = context.rectprops
    if color_res.colors is not None:
        rectprops["color"] = (
            color_res.colors(color_res.norm(subgroup.loc[idx, "_fill_"]))
            if color_res.fill_is_numeric
            else color_res.colors[subgroup.loc[idx, "_fill_"]]
        )

    rect = subgroup.loc[idx, "_rect_"]
    y0 = _NORM_SIZE - rect["y"] - rect["dy"]
    kwargs = {k: v for k, v in rectprops.items() if k != "pad"}
    patch = mpatches.Rectangle((rect["x"], y0), rect["dx"], rect["dy"], **kwargs)
    context.axes.add_patch(patch)
    return _RectDraw(patch=patch, y0=y0)


def _draw_subgroup_text(subgroup, idx, context, rect_draw):
    textprops = context.textprops
    rect = subgroup.loc[idx, "_rect_"]
    geometry = _resolve_text_geometry(context.axes, rect, rect_draw, textprops)
    label = subgroup.loc[idx, "_label_"] if context.is_leaf else _subgroup_label(idx)

    txtobj = _build_autofit_text(label, rect, geometry, textprops)
    context.axes.add_artist(txtobj)


@dataclass(frozen=True)
class _TextGeometry:
    """Position, alignment, and inset margins resolved for one subgroup label."""

    x: float
    y: float
    ha: str
    va: str
    marginx: float
    marginy: float


def _resolve_text_geometry(axes, rect, rect_draw, textprops):
    padx = textprops.get("padx", None)
    pady = textprops.get("pady", None)
    marginx = rect_draw.patch.get_linewidth() if padx is None else padx
    marginy = rect_draw.patch.get_linewidth() if pady is None else pady
    offsetx = points2dist(marginx, axes.figure.get_dpi(), axes.transData)
    offsety = points2dist(marginy, axes.figure.get_dpi(), axes.transData)

    place = textprops.get("place", "center")
    x, y, ha, va = get_position(
        (rect["x"], rect_draw.y0, rect["dx"], rect["dy"]), place, (offsetx, offsety)
    )
    return _TextGeometry(x=x, y=y, ha=ha, va=va, marginx=marginx, marginy=marginy)


def _build_autofit_text(label, rect, geometry, textprops):
    xmax = textprops.get("xmax", 1)
    ymax = textprops.get("ymax", 1)
    width, height = rect["dx"], rect["dy"]
    padx1 = geometry.marginx if xmax == 1 else 0
    pady1 = geometry.marginy if ymax == 1 else 0

    text_kwargs = {
        k: v for k, v in textprops.items() if k not in _TEXTPROPS_LAYOUT_KEYS
    }

    return _at.AutofitText(
        (geometry.x, geometry.y),
        xmax * width,
        ymax * height,
        label,
        pad=(padx1, pady1),
        reflow=textprops.get("reflow", False),
        grow=textprops.get("grow", False),
        max_fontsize=textprops.get("max_fontsize", None),
        min_fontsize=textprops.get("min_fontsize", None),
        ha=geometry.ha,
        va=geometry.va,
        **text_kwargs,
    )


def _subgroup_label(idx):
    if isinstance(idx, tuple):
        return [lbl for lbl in idx if lbl][-1]
    return idx


def points2dist(points, dpi, transform):
    inch_per_point = 1 / 72
    pixels = points * inch_per_point * dpi
    bbox = trans.Bbox([[0, 0], [pixels, 10]]).transformed(transform.inverted())
    return bbox.width


_INVALID_POSITION_MESSAGE = (
    'Invalid position. Available positions are:\n- "center", \n- "bottom left", '
    '"bottom center", "bottom right", \n- "top left", "top center", "top right".'
)


def get_position(rect, pos, pad):
    x, y, dx, dy = rect
    x_pos = {"center": x + dx / 2, "left": x + pad[0], "right": x + dx - pad[0]}
    y_pos = {"center": y + dy / 2, "bottom": y + pad[1], "top": y + dy - pad[1]}

    try:
        if pos == "center":
            return x_pos["center"], y_pos["center"], "center", "center"
        ytxt, xtxt = pos.split()
        return x_pos[xtxt], y_pos[ytxt], xtxt, ytxt
    except KeyError as exc:
        raise ValueError(_INVALID_POSITION_MESSAGE) from exc


def get_colormap(cmap, fill_col):
    if isinstance(cmap, dict):
        return cmap
    if np.issubdtype(fill_col.dtype, np.number):
        return (
            cmap if isinstance(cmap, mcolors.Colormap) else matplotlib.colormaps[cmap]
        )
    try:
        colors = matplotlib.colormaps[cmap].resampled(fill_col.nunique()).colors
    except (ValueError, KeyError):
        colors = cmap if isinstance(cmap, list) else [cmap]
    return dict(zip(fill_col.unique(), itertools.cycle(colors)))


def squarify_subgroups(data, levels, subgroup_pads):
    for i, level in enumerate(levels):
        if not i:
            data[level] = squarify_data(data[level], (0, 0, _NORM_SIZE, _NORM_SIZE))
        else:
            data[level] = _squarify_child_level(
                data, levels, i, subgroup_pads.get(level, _DEFAULT_PAD)
            )

    return data


def _squarify_child_level(data, levels, level_index, sub_pad):
    rect_colname = "_rect_"
    level = levels[level_index]
    pad_left, pad_right, pad_top, pad_bottom = resolve_pad(sub_pad)
    subgroup = data[level].copy()

    parent_idx = set(idx[:-1] for idx in subgroup.index)
    for parent in parent_idx:
        child_group = subgroup.loc[parent, :].copy()
        parent_rect = data[levels[level_index - 1]].loc[parent, rect_colname]
        is_root = not child_group.index[0]
        bounds = (
            parent_rect["x"] + (0 if is_root else pad_left),
            parent_rect["y"] + (0 if is_root else pad_bottom),
            parent_rect["dx"] - (0 if is_root else pad_left + pad_right),
            parent_rect["dy"] - (0 if is_root else pad_bottom + pad_top),
        )
        child_group = squarify_data(child_group, bounds)
        subgroup.loc[parent, rect_colname] = child_group[rect_colname].values

    return subgroup


def squarify_data(df, bounds):
    x, y, dx, dy = bounds
    area_colname = "_area_"
    rect_colname = "_rect_"
    sorted_df = df.sort_values(by=area_colname, ascending=False).copy()
    sorted_df.loc[:, rect_colname] = squarify.squarify(
        sizes=squarify.normalize_sizes(sorted_df[area_colname].values, dx, dy),
        x=x,
        y=y,
        dx=dx,
        dy=dy,
    )

    return df.loc[:, df.columns != rect_colname].join(sorted_df.loc[:, rect_colname])


def get_subgroups(data, levels):
    agg_fun = {"_area_": "sum"}
    if "_label_" in data.columns:
        agg_fun["_label_"] = "first"
    if "_fill_" in data.columns:
        agg_fun["_fill_"] = "first"

    current_level = []
    subgroups = {}
    for level in levels:
        current_level.append(level)
        subgroups[level] = data.groupby(by=current_level, dropna=False).agg(agg_fun)

    return subgroups


def get_plot_data(data, columns=None):
    columns = columns or PlotColumns()

    selected_data = _resolve_area_column(data, columns.area, columns.levels)
    selected_data = _assign_optional_column(
        selected_data, data, columns.labels, _OptionalColumnSpec("_label_", "labels")
    )
    selected_data = _assign_optional_column(
        selected_data, data, columns.fill, _OptionalColumnSpec("_fill_", "fill")
    )

    return selected_data.fillna("")


def _resolve_area_column(data, area, levels):
    if area is None:
        raise TypeError("`area` must be specified as a column name in `data`.")

    try:
        selected_data = data.loc[:, [*levels, area]].copy()
    except KeyError as exc:
        raise KeyError(
            "columns specified by `area` or `levels` not included in `data`."
        ) from exc
    return selected_data.rename(columns={area: "_area_"})


def _assign_optional_column(selected_data, data, value, spec):
    """Assign the column named `value` in `data` onto `selected_data[spec.colname]`, if given."""
    if value is None:
        return selected_data

    try:
        selected_data[spec.colname] = data.loc[:, value]
    except KeyError as exc:
        raise KeyError(
            f"column specified by `{spec.arg_name}` not included in `data`."
        ) from exc
    return selected_data
