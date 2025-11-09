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
from abc import ABC, abstractmethod
from datetime import datetime
import plotly.graph_objects as go

from report_generator.generator import report_utils
from report_generator.generator.data_models import security_dashboard_findings_portfolio_data
from report_generator.generator.data_models import security_dashboard_resolution_times_portfolio_data
from report_generator.generator.data_models import maintainability_portfolio_data
from report_generator.generator.placeholders.images.base import _AbstractImagePlaceholder

import numpy as np
import matplotlib.pyplot as plt

class _AbstractChartImagePlaceholder(_AbstractImagePlaceholder, ABC):
    DASHBOARD_EXISTING_FINDINGS_COLOR = f"#{report_utils.pptx.DASHBOARD_EXISTING_FINDINGS_COLOR}"
    DASHBOARD_NEW_FINDINGS_COLOR = f"#{report_utils.pptx.DASHBOARD_NEW_FINDINGS_COLOR}"
    DASHBOARD_RESOLVED_FINDINGS_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLVED_FINDINGS_COLOR}"

    DASHBOARD_RESOLUTION_NO_RISK_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLUTION_NO_RISK_COLOR}"
    DASHBOARD_RESOLUTION_LOW_RISK_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLUTION_LOW_RISK_COLOR}"
    DASHBOARD_RESOLUTION_MEDIUM_RISK_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLUTION_MEDIUM_RISK_COLOR}"
    DASHBOARD_RESOLUTION_HIGH_RISK_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLUTION_HIGH_RISK_COLOR}"


class _AbstractSecurityDashboardPlaceholder(_AbstractChartImagePlaceholder, ABC):
    LAYOUT = go.Layout(
        xaxis={'showline' : True, 'linewidth' : 2, 'linecolor' : '#6E7078', 'type': 'category', 'categoryorder': 'array', 'tickmode' : 'array'},
        yaxis={'showgrid' : True, 'gridwidth' : 2, 'gridcolor' : '#E0E4EF' },
        legend={'orientation' : 'h', 'yanchor' : 'top', 'xanchor' : 'center', 'y' : -0.05, 'x' : 0.5, 'traceorder' : 'normal'},
        barmode='stack'
    )
    

    @staticmethod
    @abstractmethod
    def create_portfolio():
        pass


    @staticmethod
    @abstractmethod
    def create_dashboard_with_severity(severity, width, height):
        pass


    @staticmethod
    def get_layout(keys):
        layout = _AbstractSecurityDashboardPlaceholder.LAYOUT
        layout.xaxis.update({'categoryarray' : list(keys), 'tickvals' : list(keys), 'ticktext' : _AbstractSecurityDashboardPlaceholder.transform_date_labels_to_months(keys)})
        return layout


    @staticmethod
    def create_portfolio_helper(data_source, metric, risk_entries):
        res = {"CRITICAL" : {}, "HIGH" : {}, "MEDIUM" : {}, "LOW" : {}}

        columns = []
        for entry_entry in risk_entries:
            for severity in res.keys():
                res[severity][entry_entry] = [0] * 12
        
        for system in data_source.data['systems']:
            md = maintainability_portfolio_data.get_system_metadata(system['system'])
            if not md or not md['active'] or md['isDevelopmentOnly']:
                continue
            for ratio in system[metric]:
                month = _AbstractSecurityDashboardPlaceholder.transform_date_label_to_month(ratio['month'])
                if month not in columns:
                    columns.append(month)
                month_idx = columns.index(month)

                for severity in res.keys():
                    for entry_entry in risk_entries:
                        res[severity][entry_entry][month_idx] += ratio['severities'][severity][entry_entry]
        res['columns'] = columns
        return res


    @staticmethod
    def transform_date_labels_to_months(dates):
        return [datetime.strptime(x, "%Y-%m-%d").strftime("%b") for x in dates]
    
    @staticmethod
    def transform_date_label_to_month(date):
        return datetime.strptime(date, "%Y-%m-%d").strftime("%b")


class _AbstractSecurityDashboardFindingsPlaceholder(_AbstractSecurityDashboardPlaceholder, ABC):
    @staticmethod
    def create_portfolio():
        return _AbstractSecurityDashboardPlaceholder.create_portfolio_helper(security_dashboard_findings_portfolio_data, 'findingRatio', {"resolved": 0, "existing": 0, "new": 0})

    @staticmethod
    def create_dashboard_with_severity(severity, width, height):
        portfolio_complete = _AbstractSecurityDashboardFindingsPlaceholder.create_portfolio()
        portfolio = portfolio_complete[severity]
        columns = portfolio_complete['columns']
        
        fig, ax = plt.subplots(figsize=(width,height), dpi=200, layout='constrained')

        x = np.arange(len(columns))
        w = 0.4

        ax.bar(x=x-(w/2), height=portfolio['new'], width=w, label="New")

        r = ax.bar(x=x-(w/2), height=portfolio['existing'], width=w, bottom=portfolio['new'], label="Existing")
        ax.bar_label(r, padding=2)

        # Right: grouped bar
        r = ax.bar(x=x+(w/2), height=portfolio['resolved'], width=w, label="Resolved")
        ax.bar_label(r, padding=2)

        ax.set_ylabel('Length (mm)')
        ax.set_title('Penguin attributes by species')
        ax.set_xticks(x, columns)
        ax.legend(loc='upper left', ncols=3)

        return fig

class _AbstractSecurityDashboardResolutionTimesPlaceholder(_AbstractSecurityDashboardPlaceholder, ABC):
    LEGEND_ENTRIES_PER_SEVERITY = {
        "CRITICAL" : {'noRisk' : "at most 7 days", "lowRisk" : "between 7-14 days", "mediumRisk" : "between 14-30 days", "highRisk" : "at least 30 days"},
        "HIGH" : {'noRisk' : "at most 14 days", "lowRisk" : "between 14-30 days", "mediumRisk" : "between 30-180 days", "highRisk" : "at least 180 days"},
        "MEDIUM" : {'noRisk' : "at most 30 days", "lowRisk" : "between 30-180 days", "mediumRisk" : "between 180-365 days", "highRisk" : "at least 365 days"},
        "LOW" : {'noRisk' : "at most 180 days", "lowRisk" : "between 180-365 days", "mediumRisk" : "between 1-2 years", "highRisk" : "at least 2 years"}
    }

    @staticmethod
    def create_portfolio():
        return _AbstractSecurityDashboardPlaceholder.create_portfolio_helper(security_dashboard_resolution_times_portfolio_data, 'resolutionTimes', {"noRisk": 0, "lowRisk": 0, "mediumRisk": 0, "highRisk" : 0})

    @staticmethod
    def create_dashboard_with_severity(severity, width, height):
        portfolio_complete = _AbstractSecurityDashboardResolutionTimesPlaceholder.create_portfolio()
        portfolio = portfolio_complete[severity]
        columns = portfolio_complete['columns']
        legend_entries = _AbstractSecurityDashboardResolutionTimesPlaceholder.LEGEND_ENTRIES_PER_SEVERITY[severity]

        fig, ax = plt.subplots(figsize=(width,height), dpi=200)
        bottom = np.zeros(12)

        for entry, vals in portfolio.items():
            legend_entry = legend_entries[entry]
            np_vals = np.array(vals)
            r = ax.bar(x=columns, height=np_vals, label=legend_entry, bottom=bottom)
            bottom += np_vals
        ax.bar_label(r)

        ax.set_title("Number of penguins with above average body mass")
        ax.legend(loc="upper right")
        return fig


class SecurityDashboardCriticalFindingsPlaceholder(_AbstractSecurityDashboardFindingsPlaceholder):
    """Creates a portfolio bar chart depicting the number of new, existing, and resolved critical security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_CRITICAL_FINDINGS"

    @classmethod
    def value(cls, param):
        return _AbstractSecurityDashboardFindingsPlaceholder.create_dashboard_with_severity(severity="CRITICAL", width=param['width'], height=param['height'])


class SecurityDashboardHighFindingsPlaceholder(_AbstractSecurityDashboardFindingsPlaceholder):
    """Creates a portfolio bar chart depicting the number of new, existing, and resolved high security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_HIGH_FINDINGS"

    @classmethod
    def value(cls, param):
        return _AbstractSecurityDashboardFindingsPlaceholder.create_dashboard_with_severity(severity="HIGH", width=param['width'], height=param['height'])


class SecurityDashboardMediumFindingsPlaceholder(_AbstractSecurityDashboardFindingsPlaceholder):
    """Creates a portfolio bar chart depicting the number of new, existing, and resolved medium security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_MEDIUM_FINDINGS"

    @classmethod
    def value(cls, param):
        return _AbstractSecurityDashboardFindingsPlaceholder.create_dashboard_with_severity(severity="MEDIUM", width=param['width'], height=param['height'])
    

class SecurityDashboardCriticalResolutionTimesPlaceholder(_AbstractSecurityDashboardResolutionTimesPlaceholder):
    """Creates a portfolio bar chart depicting the resolution times of critical security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_CRITICAL_RESOLUTION_TIMES"

    @classmethod
    def value(cls, param):
        return _AbstractSecurityDashboardResolutionTimesPlaceholder.create_dashboard_with_severity(severity="CRITICAL", width=param['width'], height=param['height'])
    

class SecurityDashboardHighResolutionTimesPlaceholder(_AbstractSecurityDashboardResolutionTimesPlaceholder):
    """Creates a portfolio bar chart depicting the resolution times of high security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_HIGH_RESOLUTION_TIMES"

    @classmethod
    def value(cls, param):
        return _AbstractSecurityDashboardResolutionTimesPlaceholder.create_dashboard_with_severity(severity="HIGH", width=param['width'], height=param['height'])
    

class SecurityDashboardMediumResolutionTimesPlaceholder(_AbstractSecurityDashboardResolutionTimesPlaceholder):
    """Creates a portfolio bar chart depicting the resolution times of medium security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_MEDIUM_RESOLUTION_TIMES"

    @classmethod
    def value(cls, param):
        return _AbstractSecurityDashboardResolutionTimesPlaceholder.create_dashboard_with_severity(severity="MEDIUM", width=param['width'], height=param['height'])