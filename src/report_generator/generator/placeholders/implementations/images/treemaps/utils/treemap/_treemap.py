# Originally sourced from https://github.com/chenyulue/matplotlib-extra
# Copyright (c) 2022, Chenyu Lue
# Licensed under the MIT License (see LICENSES/MIT-matplotlib-extra.txt)
#
# Modifications from the original:
# - Replaced deprecated cm.get_cmap() with matplotlib.colormaps (Matplotlib 3.9+)
# - Fixed pandas Copy-on-Write violations (pandas 2.0+)
# - Grouped layout/style keyword arguments into TreemapLayout/TreemapStyle and
#   split draw_subgroup()/get_plot_data() into focused helpers (maintainability)

import itertools
from dataclasses import dataclass, field

import matplotlib
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.transforms as trans
import numpy as np
import pandas as pd
import squarify
from matplotlib import cm

from . import _autofit_text as _at
from . import _container as trc
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


@dataclass(frozen=True)
class TreemapLayout:
    """Axes-level layout options for a treemap."""

    norm_x: int = 100
    norm_y: int = 100
    top: bool = False


@dataclass(frozen=True)
class TreemapStyle:
    """Tile/label styling, coloring, and padding for a treemap's leaf and subgroup levels."""

    cmap: object = None
    pad: object = 0.0
    split: bool = False
    rectprops: dict = field(default_factory=dict)
    textprops: dict = field(default_factory=dict)
    subgroup_rectprops: dict = field(default_factory=dict)
    subgroup_textprops: dict = field(default_factory=dict)


@dataclass(frozen=True)
class _SubgroupDrawContext:
    """Per-call context shared by the rect/text drawing helpers in draw_subgroup()."""

    axes: object
    top: bool
    norm_y: float
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


def treemap(axes, data, *, columns=None, layout=None, style=None):
    """Plot a treemap based on the `squarify` package.

    Parameters
    ----------
    axes : Axes
        The axes where the treemap will be drawn.
    data : DataFrame | list[number]
        The recommended data type is a pandas `DataFrame`. However, a list of
        numbers can also be accepted.
    columns : PlotColumns, optional
        Column selectors (area/labels/fill/levels) for `data`, by default `PlotColumns()`.
    layout : TreemapLayout, optional
        Axes normalization size and orientation, by default `TreemapLayout()`.
    style : TreemapStyle, optional
        Tile/label styling, coloring, and padding, by default `TreemapStyle()`.

    Returns
    -------
    TreemapContainer
    """
    columns = columns or PlotColumns()
    layout = layout or TreemapLayout()
    style = style or TreemapStyle()
    tr_container = trc.TreemapContainer({}, {}, handles={})

    plot_data = get_plot_data(data, columns)

    subgroups = get_subgroups(plot_data, split=style.split, levels=columns.levels)
    squarified = _squarify_treemap_subgroups(subgroups, columns.levels, layout, style)

    axes.set_xlim([0, layout.norm_x])
    axes.set_ylim([0, layout.norm_y])

    mappable = None
    for k, subgroup in squarified.items():
        context = _resolve_subgroup_draw_context(axes, k, columns.levels, layout, style)
        if context is None:
            continue
        rect_artists, text_artists, handles, mappable = draw_subgroup(subgroup, context)
        tr_container.patches[k] = rect_artists
        tr_container.texts[k] = text_artists
        tr_container.handles[k] = handles

    tr_container.mappable = mappable

    return tr_container


def _squarify_treemap_subgroups(subgroups, levels, layout, style):
    sub_pads = (
        {levels[-1]: style.rectprops.get("pad", style.pad)}
        if levels is not None
        else {}
    )
    for k, v in style.subgroup_rectprops.items():
        sub_pads[k] = v.get("pad", style.pad)
    return squarify_subgroups(
        subgroups,
        norm_x=layout.norm_x,
        norm_y=layout.norm_y,
        levels=levels,
        pad=style.pad,
        split=style.split,
        subgroup_pads=sub_pads,
    )


def _resolve_subgroup_draw_context(axes, key, levels, layout, style):
    """Build the _SubgroupDrawContext for one subgroup key, or None if it should be skipped."""
    if key in style.subgroup_rectprops:
        return _SubgroupDrawContext(
            axes=axes,
            top=layout.top,
            norm_y=layout.norm_y,
            cmap=style.cmap,
            rectprops=style.subgroup_rectprops[key],
            textprops=style.subgroup_textprops.get(key, {}),
            is_leaf=False,
        )
    if levels is None or (key == levels[-1]) or (key not in levels):
        return _SubgroupDrawContext(
            axes=axes,
            top=layout.top,
            norm_y=layout.norm_y,
            cmap=style.cmap,
            rectprops=style.rectprops,
            textprops=style.textprops,
            is_leaf=True,
        )
    return None


def draw_subgroup(subgroup, context):
    rect_artists = []
    text_artists = []
    handles_artists = None
    mappable_artists = None

    color_res = _resolve_subgroup_colors(subgroup, context.cmap)
    if color_res.colors is not None and not color_res.fill_is_numeric:
        handles_artists = [
            mpatches.Patch(color=v, label=k) for k, v in color_res.colors.items()
        ]
    elif color_res.colors is not None:
        mappable_artists = cm.ScalarMappable(color_res.norm, color_res.colors)

    for idx in subgroup.index:
        rect_draw = _draw_subgroup_rect(subgroup, idx, context, color_res)
        rect_artists.append(rect_draw.patch)

        if context.textprops and ("_label_" in subgroup.columns):
            text_artists.append(_draw_subgroup_text(subgroup, idx, context, rect_draw))

    return rect_artists, text_artists, handles_artists, mappable_artists


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
    y0 = context.norm_y - rect["y"] - rect["dy"] if context.top else rect["y"]
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
    return txtobj


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


def get_position(rect, pos, pad):
    x, y, dx, dy = rect
    x_pos = {"center": x + dx / 2, "left": x + pad[0], "right": x + dx - pad[0]}
    y_pos = {"center": y + dy / 2, "bottom": y + pad[1], "top": y + dy - pad[1]}
    name_dict = {"b": "bottom", "c": "center", "t": "top", "l": "left", "r": "right"}
    try:
        if (pos == "c") or (pos == "center") or (pos == "centre"):
            return (
                x_pos.get(pos, x_pos["center"]),
                y_pos.get(pos, y_pos["center"]),
                "center",
                "center",
            )
        elif len(pos) == 2:
            ytxt, xtxt = pos[0], pos[1]
            return (
                x_pos[name_dict[xtxt]],
                y_pos[name_dict[ytxt]],
                name_dict[xtxt],
                name_dict[ytxt],
            )
        else:
            ytxt, xtxt = pos.split()
            ytxt = "center" if ytxt == "centre" else ytxt
            xtxt = "center" if xtxt == "centre" else xtxt
            return (x_pos[xtxt], y_pos[ytxt], xtxt, ytxt)
    except KeyError as exc:
        raise ValueError(
            'Invalid position. Available positions are:\n- "center" (British spelling accepted), '
            '"center left", "center right", \n- "bottom left", "bottom center", "bottom right", '
            '\n- "top left", "top center", "top right".'
        ) from exc


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


def squarify_subgroups(
    data, norm_x, norm_y, levels=None, pad=0.0, split=False, subgroup_pads=None
):
    if subgroup_pads is None:
        subgroup_pads = {}

    if levels is None:
        for k, v in data.items():
            data[k] = squarify_data(v, (0, 0, norm_x, norm_y), split=False)
        return data

    for i, level in enumerate(levels):
        if not i:
            data[level] = squarify_data(
                data[level], (0, 0, norm_x, norm_y), split=split
            )
        else:
            data[level] = _squarify_child_level(
                data, levels, i, subgroup_pads.get(level, pad)
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
        child_group = squarify_data(child_group, bounds, split=False)
        subgroup.loc[parent, rect_colname] = child_group[rect_colname].values

    return subgroup


def squarify_data(df, bounds, split):
    x, y, dx, dy = bounds
    area_colname = "_area_"
    rect_colname = "_rect_"
    sorted_df = df.sort_values(by=area_colname, ascending=False).copy()
    if split:
        sorted_df.loc[:, rect_colname] = squarify.padded_squarify(
            sizes=squarify.normalize_sizes(sorted_df[area_colname].values, dx, dy),
            x=x,
            y=y,
            dx=dx,
            dy=dy,
        )
    else:
        sorted_df.loc[:, rect_colname] = squarify.squarify(
            sizes=squarify.normalize_sizes(sorted_df[area_colname].values, dx, dy),
            x=x,
            y=y,
            dx=dx,
            dy=dy,
        )

    return df.loc[:, df.columns != rect_colname].join(sorted_df.loc[:, rect_colname])


def get_subgroups(data, split=False, levels=None):
    if levels is None:
        return {"_group_": data}

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
        if split and level == levels[0]:
            subgroups[level] = subgroups[level].assign(_area_=1)

    return subgroups


def get_plot_data(data, columns=None):
    columns = columns or PlotColumns()
    levels = columns.levels if columns.levels is not None else []

    selected_data = _resolve_area_column(data, columns.area, levels)
    selected_data = _assign_optional_column(
        selected_data, data, columns.labels, _OptionalColumnSpec("_label_", "labels")
    )
    selected_data = _assign_optional_column(
        selected_data, data, columns.fill, _OptionalColumnSpec("_fill_", "fill")
    )

    return selected_data.fillna("")


def _resolve_area_column(data, area, levels):
    if not isinstance(data, pd.DataFrame):
        return _area_column_from_number_list(data)
    if area is None:
        raise TypeError(
            "`area` must be specified when `data` is a DataFrame. "
            "It can be a `str`, a `number` or a list of `numbers`."
        )
    if isinstance(area, str):
        return _area_column_from_column_name(data, area, levels)
    return _area_column_from_value(data, area, levels)


def _area_column_from_number_list(data):
    area_colname = "_area_"
    data_arr = np.atleast_1d(data)
    if not np.issubdtype(data_arr.dtype, np.number):
        raise ValueError("`data` must be all numbers.")
    return pd.DataFrame({area_colname: data_arr})


def _area_column_from_column_name(data, area, levels):
    area_colname = "_area_"
    try:
        selected_data = data.loc[:, [*levels, area]].copy()
    except KeyError as exc:
        raise KeyError(
            "columns specified by `area` or `levels` not included in `data`."
        ) from exc
    return selected_data.rename(columns={area: area_colname})


def _area_column_from_value(data, area, levels):
    area_colname = "_area_"
    try:
        selected_data = data.loc[:, levels].copy()
    except KeyError as exc:
        raise KeyError("columns specified by `levels` not included in `data`.") from exc

    if isinstance(area, (int, float)):
        selected_data[area_colname] = area
        return selected_data

    area_arr = np.array(area)
    if not np.issubdtype(area_arr.dtype, np.number):
        raise ValueError("`area` must be all numbers.")
    try:
        selected_data[area_colname] = area_arr
    except ValueError as exc:
        raise ValueError(
            "The length of `area` does not match the length of `data`."
        ) from exc
    return selected_data


def _assign_optional_column(selected_data, data, value, spec):
    """Assign `value` (a column name in `data`, or an array-like) onto `selected_data[spec.colname]`."""
    if value is None:
        return selected_data

    if isinstance(value, str):
        return _assign_column_by_name(selected_data, data, value, spec)

    value_arr = np.atleast_1d(value)
    try:
        selected_data[spec.colname] = value_arr
    except ValueError as exc:
        raise ValueError(
            f"The length of `{spec.arg_name}` does not match the length of `data`."
        ) from exc
    return selected_data


def _assign_column_by_name(selected_data, data, value, spec):
    try:
        selected_data[spec.colname] = data.loc[:, value]
    except KeyError as exc:
        raise KeyError(
            f"column specified by `{spec.arg_name}` not included in `data`."
        ) from exc
    except AttributeError as exc:
        raise ValueError(
            f"`data` does not support `{spec.arg_name}` specified by a string. "
            f"Specify the `{spec.arg_name}` by a list of string."
        ) from exc
    return selected_data
