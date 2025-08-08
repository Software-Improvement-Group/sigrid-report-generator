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

from abc import ABC
from typing import Callable

from pptx import Presentation

from report_generator.generator import report_utils
from report_generator.generator.data_models import maintainability_portfolio_data
from report_generator.generator.placeholders.base import Placeholder
import plotly.express as px
import io
from pptx.util import Inches

class _AbstractTreemapPlaceholder(Placeholder, ABC):

    NA_STAR_COLOR = "#b5b5b5"
    ONE_STAR_COLOR = "#db4a3d"
    TWO_STAR_COLOR = "#ef981a"
    THREE_STAR_COLOR = "#f8c640"
    FOUR_STAR_COLOR = "#57c968"
    FIVE_STAR_COLOR = "#2c963f"
    SIG_BLUE = "#243549"
    
    def translate_star_rating_to_color(rating):
        if rating == None:
            return _AbstractTreemapPlaceholder.NA_STAR_COLOR
        rating = int(rating*10)/10
        if rating < 1.5:
            return _AbstractTreemapPlaceholder.ONE_STAR_COLOR
        elif rating < 2.5:
            return _AbstractTreemapPlaceholder.TWO_STAR_COLOR
        elif rating < 3.5:
            return _AbstractTreemapPlaceholder.THREE_STAR_COLOR
        elif rating < 4.5:
            return _AbstractTreemapPlaceholder.FOUR_STAR_COLOR
        else:
            return _AbstractTreemapPlaceholder.FIVE_STAR_COLOR
    
    def translate_test_code_ratio_to_color(rating):
        if rating == None:
            return _AbstractTreemapPlaceholder.NA_STAR_COLOR
        rating = float(rating)
        if rating < 0.01:
            return _AbstractTreemapPlaceholder.ONE_STAR_COLOR
        elif rating < 0.15:
            return _AbstractTreemapPlaceholder.TWO_STAR_COLOR
        elif rating < 0.50:
            return _AbstractTreemapPlaceholder.THREE_STAR_COLOR
        elif rating < 1.50:
            return _AbstractTreemapPlaceholder.FOUR_STAR_COLOR
        else:
            return _AbstractTreemapPlaceholder.FIVE_STAR_COLOR

    @classmethod
    def resolve_pptx(cls, presentation: Presentation, key: str, value_cb: Callable):
        slides = report_utils.pptx.identify_specific_slide(presentation, key)
        if len(slides) == 0:
            return

        for slide in slides:
            shapes = report_utils.pptx.find_shapes_with_text_in_slide(slide, key)
            for shape in shapes:
                value_cb({'shape' : shape, 'slide' : slide})


class _AbstractPortfolioPlaceholder(_AbstractTreemapPlaceholder):
    def create_portfolio():
        res = {}
        system_names = maintainability_portfolio_data.system_names
        for system_name in system_names:
            md = maintainability_portfolio_data.find_system_metadata(system_name)
            if not md['active'] or md['isDevelopmentOnly']:
                continue

            res[system_name] = {
                'metadata' : md,
                'start_date_data' : maintainability_portfolio_data.start_snapshot(system_name),
                'end_date_data' : maintainability_portfolio_data.end_snapshot(system_name)
            }
        return res
    
    def create_blank_portfolio_treemap():
        names = []
        parents = []
        tracking = []

        portfolio = MaintainabilityPortfolioTreemapPlaceholder.create_portfolio()
        for s in portfolio.values():
            m = s['metadata']
            if m['teamNames'][0] not in names:
                names.append(m['teamNames'][0])
                parents.append("")
                tracking.append("")
            if m['displayName'] is not None:
                names.append(m['displayName'])
            else:
                names.append(m['systemName'])
            parents.append(m['teamNames'][0])
            tracking.append(m['systemName'])

        return {
            'names' : names,
            'parents' : parents,
            'tracking' : tracking
        }
    
    def create_treemap(shape, portfolio, treemap_data, color_mapping):
        pos_left = shape.left.inches
        pos_top = shape.top.inches
        pos_width = shape.width.inches
        pos_height = shape.height.inches
        
        values = [None] * len(treemap_data['tracking'])
        for i, t in enumerate(treemap_data['tracking']):
            cur_parent = treemap_data['parents'][i]
            if cur_parent == "":
                values[i] = 0
                if t not in color_mapping.keys():
                    color_mapping[t] = _AbstractTreemapPlaceholder.SIG_BLUE
                continue
            values[i] = portfolio[t]['end_date_data']['volumeInPersonMonths']
        
        fig = px.treemap(names=treemap_data['names'], parents=treemap_data['parents'], values=values, color=treemap_data['tracking'], color_discrete_map=color_mapping)
        fig.update_traces(root_color='rgba(250, 250, 250, 1)')
        fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))
        
        img_bytes = fig.to_image(format="jpg", width=pos_width*2*96,
                                 height=pos_height*2*96)

        return {
            'pos_left' : Inches(pos_left),
            'pos_top' : Inches(pos_top),
            'pos_width' : Inches(pos_width),
            'pos_height' : Inches(pos_height),
            'img' : img_bytes
        }


class MaintainabilityPortfolioTreemapPlaceholder(_AbstractPortfolioPlaceholder):
    """Creates a portfolio treemap where the color is determined by the maintainability rating of the individual systems."""

    key = "INTERVAL_PORTFOLIO_MAINTAINABILITY"

    @classmethod
    def value(cls, parameter=None):
        shape = parameter['shape']
        slide = parameter['slide']

        portfolio = _AbstractPortfolioPlaceholder.create_portfolio()
        treemap = _AbstractPortfolioPlaceholder.create_blank_portfolio_treemap()

        color_mapping = {}
        for t in portfolio.keys():
            color_mapping[t] = _AbstractTreemapPlaceholder.translate_star_rating_to_color(portfolio[t]['end_date_data']['maintainability'])

        data = _AbstractPortfolioPlaceholder.create_treemap(shape, portfolio, treemap, color_mapping)

        slide.shapes.add_picture(io.BytesIO(data['img']),
            left=data['pos_left'], top=data['pos_top'],
            width=data['pos_width'], height=data['pos_height'])
        
        el = shape.element
        el.getparent().remove(el)
        return 0
    
class TestCodePortfolioTreemapPlaceholder(_AbstractPortfolioPlaceholder):
    """Creates a portfolio treemap where the color is determined by the test-to-production code ratio of the individual systems."""

    key = "INTERVAL_PORTFOLIO_TEST_CODE"

    @classmethod
    def value(cls, parameter=None):
        shape = parameter['shape']
        slide = parameter['slide']

        portfolio = _AbstractPortfolioPlaceholder.create_portfolio()
        treemap = _AbstractPortfolioPlaceholder.create_blank_portfolio_treemap()

        color_mapping = {}
        for t in portfolio.keys():
            color_mapping[t] = _AbstractTreemapPlaceholder.translate_test_code_ratio_to_color(portfolio[t]['end_date_data']['testCodeRatio'])

        data = _AbstractPortfolioPlaceholder.create_treemap(shape, portfolio, treemap, color_mapping)

        slide.shapes.add_picture(io.BytesIO(data['img']),
            left=data['pos_left'], top=data['pos_top'],
            width=data['pos_width'], height=data['pos_height'])
        
        el = shape.element
        el.getparent().remove(el)
        return 0