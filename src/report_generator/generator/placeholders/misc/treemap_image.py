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
# from report_generator.generator.constants import ArchMetric, ArchSubcharacteristic, MaintMetric, MetricEnum
from report_generator.generator.data_models import architecture_data, maintainability_data, maintainability_portfolio_data
from report_generator.generator.formatters import formatters
from report_generator.generator.placeholders.base import Placeholder
import plotly.express as px
import io
from pptx.util import Inches

class _AbstractTreemapPlaceholder(Placeholder, ABC):
    """Fills this rating value, but also colors the shape the placeholder is in to correspond to the correct maintainability rating color (e.g. yellow for 3 stars)."""

    NA_STAR_COLOR = "#b5b5b5"
    ONE_STAR_COLOR = "#db4a3d"
    TWO_STAR_COLOR = "#ef981a"
    THREE_STAR_COLOR = "#f8c640"
    FOUR_STAR_COLOR = "#57c968"
    FIVE_STAR_COLOR = "#2c963f"
    SIG_BLUE = "#243549"

    TREEMAP_WIDTH_PIXELS = 1900
    TREEMAP_HEIGHT_PIXELS = 617

    @classmethod
    def resolve_pptx(cls, presentation: Presentation, key: str, value_cb: Callable):
        slides = report_utils.pptx.identify_specific_slide(presentation, key)
        if len(slides) == 0:
            return

        for slide in slides:
            paragraphs = report_utils.pptx.find_text_in_slide(slide, key)
            for paragraph in paragraphs:
                value_cb({'parameter' : paragraph.text, 'slide' : slide})

        # rating = value_cb()

        # rating_color = report_utils.pptx.determine_rating_color(rating)
        # rating_rounded = formatters.maintainability_round(rating)

        # for shape in shapes:
        #     report_utils.pptx.set_shape_color(shape, rating_color)

        # report_utils.pptx.update_many_paragraphs(paragraphs, key, rating_rounded)


class MaintainabilityPortfolioTreemapPlaceholder(_AbstractTreemapPlaceholder):
    key = "INTERVAL_PORTFOLIO_MAINTAINABILITY"

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
    
    def create_portfolio_treemap():
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

    def translate_star_rating_to_color(rating):
        rating = int(rating*10)/10
        if rating < 1.5:
            return MaintainabilityPortfolioTreemapPlaceholder.ONE_STAR_COLOR
        elif rating < 2.5:
            return MaintainabilityPortfolioTreemapPlaceholder.TWO_STAR_COLOR
        elif rating < 3.5:
            return MaintainabilityPortfolioTreemapPlaceholder.THREE_STAR_COLOR
        elif rating < 4.5:
            return MaintainabilityPortfolioTreemapPlaceholder.FOUR_STAR_COLOR
        else:
            return MaintainabilityPortfolioTreemapPlaceholder.FIVE_STAR_COLOR

    @classmethod
    def value(cls, parameter=None):
        # print(f"parameter: {parameter}")
        # res = MaintainabilityPortfolioTreemapPlaceholder.create_portfolio()
        # system_names = maintainability_portfolio_data.system_names
        # for system_name in system_names:
        #     start_snapshot = maintainability_portfolio_data.start_snapshot(system_name)
        #     end_snapshot = maintainability_portfolio_data.end_snapshot(system_name)

        #     print(f"{system_name} start: {start_snapshot}")
        #     print(f"{system_name} end: {end_snapshot}")
        #     break
        # return parameter
        # split_param = parameter['parameter'].split(":")
        # pos_left = split_param[1]
        # pos_top = split_param[2]
        # pos_width = split_param[3]
        pos_left = 0.56
        pos_top = 3.5
        pos_width = 9.57
        pos_height = None
        # if len(split_param) == 5:
        #     pos_height = split_param[4]
        portfolio = MaintainabilityPortfolioTreemapPlaceholder.create_portfolio()
        treemap = MaintainabilityPortfolioTreemapPlaceholder.create_portfolio_treemap()

        values = [None] * len(treemap['tracking'])
        color_mapping = {}
        for i, t in enumerate(treemap['tracking']):
            cur_parent = treemap['parents'][i]
            if cur_parent == "":
                values[i] = 0
                if t not in color_mapping.keys():
                    color_mapping[t] = MaintainabilityPortfolioTreemapPlaceholder.SIG_BLUE
                continue
            values[i] = portfolio[t]['end_date_data']['volumeInPersonMonths']
            color_mapping[t] = MaintainabilityPortfolioTreemapPlaceholder.translate_star_rating_to_color(portfolio[t]['end_date_data']['maintainability'])

        fig = px.treemap(names=treemap['names'], parents=treemap['parents'], values=values, color=treemap['tracking'], color_discrete_map=color_mapping)
        fig.update_traces(root_color='rgba(250, 250, 250, 1)')
        fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))

        img_bytes = fig.to_image(format="jpg", width=MaintainabilityPortfolioTreemapPlaceholder.TREEMAP_WIDTH_PIXELS,
                                 height=MaintainabilityPortfolioTreemapPlaceholder.TREEMAP_HEIGHT_PIXELS)

        print(f"{pos_left} {pos_top} {pos_width} {pos_height}")
        parameter['slide'].shapes.add_picture(io.BytesIO(img_bytes),
            left=Inches(pos_left), top=Inches(pos_top),
            width=Inches(pos_width))
        # return {
        #     'pos_left' : pos_left,
        #     'pos_top' : pos_top,
        #     'pos_width' : pos_width,
        #     'pos_height' : pos_height,
        #     'img' : img_bytes
        # }
        return 0
