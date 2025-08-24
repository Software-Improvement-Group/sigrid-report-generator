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

from report_generator.generator import report_utils
from report_generator.generator.data_models import security_dashboard_findings_portfolio_data, maintainability_portfolio_data
from report_generator.generator.placeholders.base import Placeholder
import plotly.graph_objects as go
import io
import logging
from pptx.util import Inches
from datetime import datetime

class _AbstractChartImagePlaceholder(Placeholder):
    SIG_BLUE_COLOR = f"#{report_utils.pptx.SIG_BLUE_COLOR}"
    NA_STAR_COLOR = f"#{report_utils.pptx.NA_STAR_COLOR}"

    DASHBOARD_EXISTING_FINDINGS_COLOR = f"#{report_utils.pptx.DASHBOARD_EXISTING_FINDINGS_COLOR}"
    DASHBOARD_NEW_FINDINGS_COLOR = f"#{report_utils.pptx.DASHBOARD_NEW_FINDINGS_COLOR}"
    DASHBOARD_RESOLVED_FINDINGS_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLVED_FINDINGS_COLOR}"

    DASHBOARD_RESOLUTION_QUICK_COLOR = DASHBOARD_EXISTING_FINDINGS_COLOR
    DASHBOARD_RESOLUTION_SLOW_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLUTION_SLOW_COLOR}"
    DASHBOARD_RESOLUTION_LONG_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLUTION_LONG_COLOR}"
    DASHBOARD_RESOLUTION_LONGEST_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLUTION_LONGEST_COLOR}"

    @classmethod
    def resolve_pptx(cls, presentation: Presentation, key: str, value_cb: Callable):
        slides = report_utils.pptx.identify_specific_slide(presentation, key)
        if len(slides) == 0:
            return

        for slide in slides:
            shapes = report_utils.pptx.find_shapes_with_text_in_slide(slide, key)
            for shape in shapes:
                fig = value_cb()
                cls.create_and_add_treemap_image_to_slide(shape, slide, fig)
    
    @staticmethod
    def create_and_add_treemap_image_to_slide(shape_placeholder, slide, fig):
        pos_left = shape_placeholder.left.inches
        pos_top = shape_placeholder.top.inches
        pos_width = shape_placeholder.width.inches
        pos_height = shape_placeholder.height.inches

        # fig = px.treemap(names=data['names'], parents=data['parents'], values=data['values'], color=data['color'], color_discrete_map=data['color_mapping'])
        # fig.update_traces(root_color='rgba(250, 250, 250, 1)')
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


class _AbstractSecurityDashboardPlaceholder(_AbstractChartImagePlaceholder):
    LAYOUT = go.Layout(
        xaxis={
            'showline' : True,
            'linewidth' : 2,
            'linecolor' : '#6E7078',
            'type': 'category',
            'categoryorder': 'array',
            'tickmode' : 'array'
            # 'title': {
            #     'text': 'Month'
            # }
        },
        yaxis={
            'showgrid' : True,
            'gridwidth' : 2,
            'gridcolor' : '#E0E4EF'
        },
        legend={
            'orientation' : 'h',
            'yanchor' : 'top',
            'xanchor' : 'center',
            'y' : -0.02,
            'x' : 0.5
        },
        barmode='stack'
    )

    @staticmethod
    def transform_date_labels_to_months(dates):
        return [datetime.strptime(x, "%Y-%m-%d").strftime("%b") for x in dates]

class _AbstractSecurityDashboardFindingsPlaceholder(_AbstractSecurityDashboardPlaceholder):
    @staticmethod
    def create_portfolio():
        res = {"CRITICAL" : {}, "HIGH" : {}, "MEDIUM" : {}, "LOW" : {}}
        for system in security_dashboard_findings_portfolio_data.data['systems']:
            md = maintainability_portfolio_data.find_system_metadata(system['system'])
            if not md or not md['active'] or md['isDevelopmentOnly']:
                continue
            for ratio in system['findingRatio']:
                month = ratio['month']
                for severity in res.keys():
                    if month not in res[severity].keys():
                        res[severity][month] = {"resolved": 0, "existing": 0, "new": 0}
                    for status in res[severity][month].keys():
                        res[severity][month][status] += ratio['severities'][severity][status]
        return res
    
    @staticmethod
    def create_dashboard_with_severity(severity):
        portfolio = _AbstractSecurityDashboardFindingsPlaceholder.create_portfolio()[severity]

        y_values_new = [portfolio[k]['new'] for k in portfolio.keys()]
        y_values_existing = [portfolio[k]['existing'] for k in portfolio.keys()]
        y_values_resolved = [portfolio[k]['resolved'] for k in portfolio.keys()]
        open_findings_text_values = [x + y for x, y in zip(y_values_new, y_values_existing)]
        data = [
            go.Bar(
                x=list(portfolio.keys()),
                y=y_values_new,
                name="New",
                marker_color=_AbstractChartImagePlaceholder.DASHBOARD_NEW_FINDINGS_COLOR,
                offsetgroup="open"
            ),
            go.Bar(
                x=list(portfolio.keys()),
                y=y_values_existing,
                name="Existing",
                marker_color=_AbstractChartImagePlaceholder.DASHBOARD_EXISTING_FINDINGS_COLOR,
                offsetgroup="open",
                textposition="outside",
                text=open_findings_text_values
            ),
            go.Bar(
                x=list(portfolio.keys()),
                y=y_values_resolved,
                name="Resolved",
                marker_color=_AbstractChartImagePlaceholder.DASHBOARD_RESOLVED_FINDINGS_COLOR,
                offsetgroup="closed",
                textposition="outside",
                text=y_values_resolved
            ),
        ]

        layout = _AbstractSecurityDashboardPlaceholder.LAYOUT
        layout.xaxis.update({
            'categoryarray' : list(portfolio.keys()),
            'tickvals' : list(portfolio.keys()),
            'ticktext' : _AbstractSecurityDashboardPlaceholder.transform_date_labels_to_months(portfolio.keys())
        })

        return go.Figure(data=data, layout=layout)


class SecurityDashboardCriticalFindingsPlaceholder(_AbstractSecurityDashboardFindingsPlaceholder):
    """Creates a portfolio treemap where the color is determined by the maintainability rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_CRITICAL_FINDINGS"

    @classmethod
    def value(cls, parameter=None):
        return _AbstractSecurityDashboardFindingsPlaceholder.create_dashboard_with_severity("CRITICAL")


class SecurityDashboardHighFindingsPlaceholder(_AbstractSecurityDashboardFindingsPlaceholder):
    """Creates a portfolio treemap where the color is determined by the maintainability rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_HIGH_FINDINGS"

    @classmethod
    def value(cls, parameter=None):
        return _AbstractSecurityDashboardFindingsPlaceholder.create_dashboard_with_severity("HIGH")


class SecurityDashboardMediumFindingsPlaceholder(_AbstractSecurityDashboardFindingsPlaceholder):
    """Creates a portfolio treemap where the color is determined by the maintainability rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_MEDIUM_FINDINGS"

    @classmethod
    def value(cls, parameter=None):
        return _AbstractSecurityDashboardFindingsPlaceholder.create_dashboard_with_severity("MEDIUM")