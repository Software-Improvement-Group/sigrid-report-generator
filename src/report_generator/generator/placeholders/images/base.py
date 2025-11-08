#  Copyright Software Improvement Group
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from typing import Callable
from abc import ABC

from pptx.presentation import Presentation

from report_generator.generator.placeholders.base import Placeholder, PlaceholderDocType
from report_generator.generator import report_utils

import io
from pptx.util import Inches

import pandas as pd
import matplotlib.pyplot as plt
import mpl_extra.treemap as tr

class _AbstractImagePlaceholder(Placeholder, ABC):
    __doc_type__ = PlaceholderDocType.IMAGE
    BUNDLE_COLOR = f"#{report_utils.pptx.SIG_GREY_COLOR}"
    NA_STAR_COLOR = f"#{report_utils.pptx.NA_STAR_COLOR}"

    @classmethod
    def resolve_pptx(cls, presentation: Presentation, key: str, value_cb: Callable):
        shapes = report_utils.pptx.find_shapes(presentation, key)
        if len(shapes) == 0:
            return

        fig_data = value_cb()
        for shape in shapes:
            cls.create_and_add_image_to_slide(shape, fig_data)
    
    @staticmethod
    def create_and_add_image_to_slide(shape_placeholder, fig_data):
        pos_left = shape_placeholder.left.inches
        pos_top = shape_placeholder.top.inches
        pos_width = shape_placeholder.width.inches
        pos_height = shape_placeholder.height.inches

        fig = _AbstractImagePlaceholder.MAPPER[fig_data['figure_type']](pos_width, pos_height, fig_data)

        buf = io.BytesIO()
        fig.savefig(buf, dpi='figure', bbox_inches='tight')
        buf.seek(0)
        
        shape_placeholder.part.slide.shapes.add_picture(io.BytesIO(buf.getvalue()),
            left=Inches(pos_left), top=Inches(pos_top),
            width=Inches(pos_width), height=Inches(pos_height))

        el = shape_placeholder.element
        el.getparent().remove(el)

        buf.close()
        plt.close(fig)

    @staticmethod
    def _draw_treemap(width, height, fig_data):
        fig, ax = plt.subplots(figsize=(width,height), dpi=200)
        subkeys = ["system_names", "volumes", "labels", "roots"]
        df = pd.DataFrame({k: fig_data[k] for k in subkeys})
        tr.treemap(axes=ax, data=df, area="volumes", levels=["roots", "system_names"], top=True,
                fill="system_names", cmap=fig_data['color_mapping'], labels="labels",
                rectprops={'ec':'w', 'pad':(0,0,0,2)},
                textprops={
                    'fontfamily':'sans-serif', 'reflow':True, 'place':'center', 'grow':True,
                    'max_fontsize':4, 'color':'k', 'pady':1, 'padx':1}, # Text inside squares
                subgroup_rectprops={'roots':{'ec':'w', 'fc':_AbstractImagePlaceholder.BUNDLE_COLOR}},
                subgroup_textprops={'roots':{'place':'top center', 'max_fontsize':3, 'pady':5, 'fontfamily':'sans-serif', 'color':'k'}}
        )
        ax.axis("off")
        return fig
    
    @staticmethod
    def _draw_barchart(width, height, fig_data):
        pass

_AbstractImagePlaceholder.MAPPER = {
    'treemap': _AbstractImagePlaceholder._draw_treemap,
    'barchart': _AbstractImagePlaceholder._draw_barchart
}