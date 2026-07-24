# Originally sourced from https://github.com/chenyulue/matplotlib-extra
# Copyright (c) 2022, Chenyu Lue
# Licensed under the MIT License (see LICENSES/MIT-matplotlib-extra.txt)
#
# Modifications from the original:
# - Replaced deprecated cm.get_cmap() with matplotlib.colormaps (Matplotlib 3.9+)
# - Fixed pandas Copy-on-Write violations (pandas 2.0+)

import itertools

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


def treemap(
    axes,
    data,
    *,
    area=None,
    labels=None,
    fill=None,
    cmap=None,
    levels=None,
    norm_x=100,
    norm_y=100,
    top=False,
    pad=0.0,
    split=False,
    subgroup_rectprops=None,
    subgroup_textprops=None,
    rectprops=None,
    textprops=None,
):
    """Plot a treemap based on the `squarify` package.

    Parameters
    ----------
    axes : Axes
        The axes where the treemap will be drawn.
    data : DataFrame | list[number]
        The recommended data type is a pandas `DataFrame`. However, a list of
        numbers can also be accepted.
    area : None | int | float | str | list[number], optional
        If `data` is a `DataFrame`, `area` cannot be `None`. If `data` is a list
        of numbers, `area` won't take effect.
    labels : None | str | list[str], optional
        Specify the column in the data (`DataFrame`) used as labels for the leaf
        tiles, by default None.
    fill : None | str | list, optional
        Specify the column in the data (`DataFrame`) used to determine the fill
        color for the leaf tiles, by default None.
    cmap : None | str | dict | list, optional
        Color mapping for fill values, by default None.
    levels : None | list[str], optional
        Hierarchical column names for multi-level treemaps, by default None.
    norm_x : int, optional
        x normalization value for squarify, by default 100.
    norm_y : int, optional
        y normalization value for squarify, by default 100.
    top : bool, optional
        If True, the treemap will be upside down, by default False.
    pad : float | a 2- or 4-tuple of float, optional
        Global tile padding in data coordinates, by default 0.0.
    split : bool, optional
        If True, split into equal-sized root tiles, by default False.
    subgroup_rectprops : dict of dict, optional
        Tile properties for non-leaf levels, by default None.
    subgroup_textprops : dict of dict, optional
        Label properties for non-leaf levels, by default None.
    rectprops : dict, optional
        Tile properties for the leaf level, by default None.
    textprops : dict, optional
        Label properties for the leaf level, by default None.

    Returns
    -------
    TreemapContainer
    """
    tr_container = trc.TreemapContainer({}, {}, handles={})

    if rectprops is None:
        rectprops = {}
    if textprops is None:
        textprops = {}

    if subgroup_rectprops is None:
        subgroup_rectprops = {}
    if subgroup_textprops is None:
        subgroup_textprops = {}

    plot_data = get_plot_data(
        data=data, area=area, labels=labels, fill=fill, levels=levels
    )

    subgroups = get_subgroups(plot_data, split=split, levels=levels)

    sub_pads = {levels[-1]: rectprops.get("pad", pad)} if levels is not None else {}
    for k, v in subgroup_rectprops.items():
        sub_pads[k] = v.get("pad", pad)
    squarified = squarify_subgroups(
        subgroups,
        norm_x=norm_x,
        norm_y=norm_y,
        levels=levels,
        pad=pad,
        split=split,
        subgroup_pads=sub_pads,
    )

    axes.set_xlim([0, norm_x])
    axes.set_ylim([0, norm_y])

    mappable = None
    for k, subgroup in squarified.items():
        if k in subgroup_rectprops:
            rect_artists, text_artists, handles, mappable = draw_subgroup(
                axes,
                subgroup,
                top,
                norm_y,
                cmap,
                subgroup_rectprops[k],
                subgroup_textprops.get(k, {}),
                False,
            )
            tr_container.patches[k] = rect_artists
            tr_container.texts[k] = text_artists
            tr_container.handles[k] = handles
        elif levels is None or (k == levels[-1]) or (k not in levels):
            rect_artists, text_artists, handles, mappable = draw_subgroup(
                axes, subgroup, top, norm_y, cmap, rectprops, textprops, True
            )
            tr_container.patches[k] = rect_artists
            tr_container.texts[k] = text_artists
            tr_container.handles[k] = handles

    tr_container.mappable = mappable

    return tr_container


def draw_subgroup(axes, subgroup, top, norm_y, cmap, rectprops, textprops, is_leaf):
    rect_artists = []
    text_artists = []
    handles_artists = None
    mappable_artists = None

    if "_fill_" in subgroup.columns:
        colors = get_colormap(cmap, subgroup["_fill_"])
        fill_is_numeric = pd.api.types.is_numeric_dtype(subgroup.loc[:, "_fill_"].dtype)
        if fill_is_numeric:
            max_value = subgroup["_fill_"].max()
            min_value = subgroup["_fill_"].min()
            norm = mcolors.Normalize(vmin=min_value, vmax=max_value)
            mappable_artists = cm.ScalarMappable(norm, colors)
        else:
            handles_artists = [
                mpatches.Patch(color=v, label=k) for k, v in colors.items()
            ]

    for idx in subgroup.index:
        if ("_fill_" in subgroup.columns) and fill_is_numeric:
            rectprops["color"] = colors(norm(subgroup.loc[idx, "_fill_"]))
        elif "_fill_" in subgroup.columns:
            rectprops["color"] = colors[subgroup.loc[idx, "_fill_"]]

        rect = subgroup.loc[idx, "_rect_"]
        y0 = norm_y - rect["y"] - rect["dy"] if top else rect["y"]
        kwargs = {k: v for k, v in rectprops.items() if k != "pad"}
        patch = mpatches.Rectangle((rect["x"], y0), rect["dx"], rect["dy"], **kwargs)
        axes.add_patch(patch)

        rect_artists.append(patch)

        if textprops and ("_label_" in subgroup.columns):
            extra = [
                "grow",
                "reflow",
                "xmax",
                "ymax",
                "place",
                "max_fontsize",
                "min_fontsize",
                "padx",
                "pady",
            ]
            grow = textprops.get("grow", False)
            reflow = textprops.get("reflow", False)
            xmax = textprops.get("xmax", 1)
            ymax = textprops.get("ymax", 1)
            place = textprops.get("place", "center")
            max_fontsize = textprops.get("max_fontsize", None)
            min_fontsize = textprops.get("min_fontsize", None)
            padx = textprops.get("padx", None)
            pady = textprops.get("pady", None)

            xa0, ya0, width, height = rect["x"], y0, rect["dx"], rect["dy"]

            marginx = patch.get_linewidth() if padx is None else padx
            marginy = patch.get_linewidth() if pady is None else pady
            offsetx = points2dist(marginx, axes.figure.get_dpi(), axes.transData)
            offsety = points2dist(marginy, axes.figure.get_dpi(), axes.transData)
            (x, y, ha, va) = get_position(
                xa0, ya0, width, height, place, (offsetx, offsety)
            )

            text_kwargs = {k: v for k, v in textprops.items() if k not in extra}

            padx1 = marginx if xmax == 1 else 0
            pady1 = marginy if ymax == 1 else 0

            if is_leaf:
                txtobj = _at.AutofitText(
                    (x, y),
                    xmax * width,
                    ymax * height,
                    subgroup.loc[idx, "_label_"],
                    pad=(padx1, pady1),
                    reflow=reflow,
                    grow=grow,
                    max_fontsize=max_fontsize,
                    min_fontsize=min_fontsize,
                    ha=ha,
                    va=va,
                    **text_kwargs,
                )
            else:
                if isinstance(idx, tuple):
                    subgroup_label = [lbl for lbl in idx if lbl][-1]
                else:
                    subgroup_label = idx
                txtobj = _at.AutofitText(
                    (x, y),
                    xmax * width,
                    ymax * height,
                    subgroup_label,
                    pad=(padx1, pady1),
                    reflow=reflow,
                    grow=grow,
                    max_fontsize=max_fontsize,
                    min_fontsize=min_fontsize,
                    ha=ha,
                    va=va,
                    **text_kwargs,
                )

            axes.add_artist(txtobj)

            text_artists.append(txtobj)

    return rect_artists, text_artists, handles_artists, mappable_artists


def points2dist(points, dpi, transform):
    inch_per_point = 1 / 72
    pixels = points * inch_per_point * dpi
    bbox = trans.Bbox([[0, 0], [pixels, 10]]).transformed(transform.inverted())
    return bbox.width


def get_position(x, y, dx, dy, pos, pad):
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
    data,
    norm_x,
    norm_y,
    levels=None,
    pad=0.0,
    split=False,
    subgroup_pads=None,
):
    rect_colname = "_rect_"

    if subgroup_pads is None:
        subgroup_pads = {}

    if levels is None:
        for k, v in data.items():
            data[k] = squarify_data(v, x=0, y=0, dx=norm_x, dy=norm_y, split=False)
        return data

    for i, level in enumerate(levels):
        subgroup = data[level]
        if not i:
            data[level] = squarify_data(
                subgroup, x=0, y=0, dx=norm_x, dy=norm_y, split=split
            )
        else:
            sub_pad = subgroup_pads.get(level, pad)
            pad_left, pad_right, pad_top, pad_bottom = get_surrounding_pad(sub_pad)
            subgroup = data[level].copy()
            parent_idx = set(idx[:-1] for idx in subgroup.index)
            for parent in parent_idx:
                child_group = subgroup.loc[parent, :].copy()
                parent_rect = data[levels[i - 1]].loc[parent, rect_colname]
                x, y, dx, dy = (
                    parent_rect["x"],
                    parent_rect["y"],
                    parent_rect["dx"],
                    parent_rect["dy"],
                )
                child_group = squarify_data(
                    child_group,
                    x + (0 if (not child_group.index[0]) else pad_left),
                    y + (0 if (not child_group.index[0]) else pad_bottom),
                    dx - (0 if (not child_group.index[0]) else pad_left + pad_right),
                    dy - (0 if (not child_group.index[0]) else pad_bottom + pad_top),
                    split=False,
                )
                subgroup.loc[parent, rect_colname] = child_group[rect_colname].values
            data[level] = subgroup

    return data


def get_surrounding_pad(pad):
    if isinstance(pad, (int, float)):
        pad_left, pad_right, pad_top, pad_bottom = pad, pad, pad, pad
    elif isinstance(pad, tuple) and (len(pad) == 2):
        pad_left, pad_top = pad
        pad_right, pad_bottom = pad
    elif isinstance(pad, tuple) and (len(pad) == 4):
        pad_left, pad_right, pad_top, pad_bottom = pad
    else:
        raise ValueError(
            "`pad` can only be a number, or a tuple of two or four numbers."
        )

    return pad_left, pad_right, pad_top, pad_bottom


def squarify_data(df, x, y, dx, dy, split):
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


def get_plot_data(data, area=None, labels=None, fill=None, levels=None):
    if levels is None:
        levels = []

    area_colname = "_area_"
    label_colname = "_label_"
    fill_colname = "_fill_"

    if isinstance(data, pd.DataFrame):
        if area is None:
            raise TypeError(
                "`area` must be specified when `data` is a DataFrame. "
                "It can be a `str`, a `number` or a list of `numbers`."
            )

        if isinstance(area, str):
            try:
                selected_data = data.loc[:, [*levels, area]].copy()
            except KeyError as exc:
                raise KeyError(
                    "columns specified by `area` or `levels` not included in `data`."
                ) from exc

            selected_data = selected_data.rename(columns={area: area_colname})

        elif isinstance(area, (int, float)):
            try:
                selected_data = data.loc[:, levels].copy()
            except KeyError as exc:
                raise KeyError(
                    "columns specified by `levels` not included in `data`."
                ) from exc
            selected_data[area_colname] = area

        else:
            try:
                selected_data = data.loc[:, levels].copy()
            except KeyError as exc:
                raise KeyError(
                    "columns specified by `levels` not included in `data`."
                ) from exc

            area_arr = np.array(area)

            if np.issubdtype(area_arr.dtype, np.number):
                try:
                    selected_data[area_colname] = area_arr
                except ValueError as exc:
                    raise ValueError(
                        "The length of `area` does not match the length of `data`."
                    ) from exc
            else:
                raise ValueError("`area` must be all numbers.")

    else:
        data_arr = np.atleast_1d(data)
        if np.issubdtype(data_arr.dtype, np.number):
            selected_data = pd.DataFrame({"_area_": data_arr})
        else:
            raise ValueError("`data` must be all numbers.")

    if isinstance(labels, str):
        try:
            selected_data[label_colname] = data.loc[:, labels]
        except KeyError as exc:
            raise KeyError(
                "column specified by `labels` not included in `data`."
            ) from exc
        except AttributeError as exc:
            raise ValueError(
                "`data` does not support `labels` specified by a string. "
                "Specify the `labels` by a list of string."
            ) from exc
    elif labels is not None:
        label_arr = np.atleast_1d(labels)
        try:
            selected_data[label_colname] = label_arr
        except ValueError as exc:
            raise ValueError(
                "The length of `labels` does not match the length of `data`."
            ) from exc

    if isinstance(fill, str):
        try:
            selected_data[fill_colname] = data.loc[:, fill]
        except KeyError as exc:
            raise KeyError(
                "column specified by `fill` not included in `data`."
            ) from exc
        except AttributeError as exc:
            raise ValueError(
                "`data` does not support `fill` specified by a string. "
                "Specify the `fill` by a list."
            ) from exc
    elif fill is not None:
        fill_arr = np.atleast_1d(fill)
        try:
            selected_data[fill_colname] = fill_arr
        except ValueError as exc:
            raise ValueError(
                "The length of `fill` does not match the length of `data`."
            ) from exc

    return selected_data.fillna("")
