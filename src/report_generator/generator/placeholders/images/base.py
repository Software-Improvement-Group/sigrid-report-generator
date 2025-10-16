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

from pptx import Presentation

from report_generator.generator.placeholders.base import Placeholder
from report_generator.generator import report_utils

import io
from pptx.util import Inches

class _AbstractImagePlaceholder(Placeholder):
    BUNDLE_COLOR = f"#{report_utils.pptx.SIG_GREY_COLOR}"
    NA_STAR_COLOR = f"#{report_utils.pptx.NA_STAR_COLOR}"

    @classmethod
    def resolve_pptx(cls, presentation: Presentation, key: str, value_cb: Callable):
        slides = report_utils.pptx.identify_specific_slide(presentation, key)
        if len(slides) == 0:
            return

        for slide in slides:
            shapes = report_utils.pptx.find_shapes_with_text_in_slide(slide, key)
            for shape in shapes:
                fig = value_cb()
                cls.create_and_add_image_to_slide(shape, slide, fig)
    
    @staticmethod
    def create_and_add_image_to_slide(shape_placeholder, slide, fig):
        pos_left = shape_placeholder.left.inches
        pos_top = shape_placeholder.top.inches
        pos_width = shape_placeholder.width.inches
        pos_height = shape_placeholder.height.inches

        fig.update_layout(
            margin = dict(t=0, l=0, r=0, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        
        img_bytes = fig.to_image(format="png", width=pos_width*2*96, height=pos_height*2*96)
        
        slide.shapes.add_picture(io.BytesIO(img_bytes),
            left=Inches(pos_left), top=Inches(pos_top),
            width=Inches(pos_width), height=Inches(pos_height))

        el = shape_placeholder.element
        el.getparent().remove(el)