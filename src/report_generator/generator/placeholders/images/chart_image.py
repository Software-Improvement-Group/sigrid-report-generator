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

from report_generator.generator import report_utils
from report_generator.generator.data_models import security_dashboard_findings_portfolio_data
from report_generator.generator.data_models import security_dashboard_resolution_times_portfolio_data
from report_generator.generator.data_models import maintainability_portfolio_data
from report_generator.generator.placeholders.images.base import _AbstractImagePlaceholder

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

class _AbstractSecurityDashboardPlaceholder(_AbstractImagePlaceholder, ABC):
    @staticmethod
    @abstractmethod
    def create_portfolio():
        pass


    @staticmethod
    @abstractmethod
    def create_dashboard_with_severity(severity, width, height):
        pass

    
    @classmethod
    def _determine_columns(cls, data_source, metric):
        columns: list[str] = []
        for system in data_source.data['systems']:
            md = maintainability_portfolio_data.get_system_metadata(system['system'])
            if not md or not md['active'] or md['isDevelopmentOnly']:
                continue
            for ratio in system[metric]:
                month = cls._transform_date_label_to_month(ratio['month'])
                if month not in columns:
                    columns.append(month)
        return columns


    @classmethod
    def create_portfolio_helper(cls, data_source, metric, risk_entries):
        columns: list[str] = cls._determine_columns(data_source=data_source, metric=metric)
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        portfolio = {severity : {risk: [0] * len(columns) for risk in risk_entries} for severity in severities}

        for system in data_source.data['systems']:
            md = maintainability_portfolio_data.get_system_metadata(system['system'])
            if not md or not md['active'] or md['isDevelopmentOnly']:
                continue
            cls._process_system(system=system, metric=metric, columns=columns, severities=severities, risk_entries=risk_entries, portfolio=portfolio)
        portfolio['columns'] = columns
        return portfolio


    @classmethod
    def _process_system(cls, system: dict, metric: str, columns: list[str], severities: list[str], risk_entries: list[str], portfolio: dict):
        for ratio in system[metric]:
            month = cls._transform_date_label_to_month(ratio['month'])
            month_idx = columns.index(month)

            for severity in severities:
                for risk_entry in risk_entries:
                    portfolio[severity][risk_entry][month_idx] += ratio['severities'][severity][risk_entry]


    @staticmethod
    def _transform_date_label_to_month(date):
        return datetime.strptime(date, "%Y-%m-%d").strftime("%b")

    
    @staticmethod
    def _calculate_sensible_ticker_interval(y_max, target_ticks=6):
        """
        Calculate a 'nice' interval for axis ticks, aiming for target_ticks.
        Uses multipliers of 1, 2, 5, and powers of ten to find a suitable step.
        """
        if target_ticks < 1:
            target_ticks = 6
        y_max = max(1, y_max)
        raw_interval = y_max / target_ticks
        for _ in range(4):
            p = 10 ** int(np.floor(np.log10(raw_interval)))
            for m in [1, 2, 5]:
                step = m * p
                if step >= raw_interval:
                    return int(step)
        return int(raw_interval)
    
    @classmethod
    def _format_image(cls, ax, x, columns, max_value):
        if max_value <= 1:
            max_value = 1
        ax.set_xticks(x, columns)
        ax.set_ylim(0, int(max_value*1.15))
        ticker_interval = cls._calculate_sensible_ticker_interval(max_value)
        ax.yaxis.set_major_locator(ticker.MultipleLocator(ticker_interval))
        ax.legend(loc='upper center', ncols=4, bbox_to_anchor=(0.5, -0.15), fontsize=6)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="both", labelsize=8)
        ax.yaxis.grid(True, color="#E0E4EF", zorder=0)


class _AbstractSecurityDashboardFindingsPlaceholder(_AbstractSecurityDashboardPlaceholder, ABC):
    DASHBOARD_EXISTING_FINDINGS_COLOR = f"#{report_utils.pptx.DASHBOARD_EXISTING_FINDINGS_COLOR}"
    DASHBOARD_NEW_FINDINGS_COLOR = f"#{report_utils.pptx.DASHBOARD_NEW_FINDINGS_COLOR}"
    DASHBOARD_RESOLVED_FINDINGS_COLOR = f"#{report_utils.pptx.DASHBOARD_RESOLVED_FINDINGS_COLOR}"

    @classmethod
    def create_portfolio(cls):
        return cls.create_portfolio_helper(security_dashboard_findings_portfolio_data, 'findingRatio', {"resolved": 0, "existing": 0, "new": 0})

    @classmethod
    def create_dashboard_with_severity(cls, severity, width, height):
        portfolio_complete = cls.create_portfolio()
        portfolio = portfolio_complete[severity]
        columns = portfolio_complete['columns']
        
        fig, ax = plt.subplots(figsize=(width,height), dpi=200, facecolor="none")

        x = np.arange(len(columns))
        w = 0.4

        ax.bar(x=x-(w/2), height=portfolio['new'], width=w, label="New", color=cls.DASHBOARD_NEW_FINDINGS_COLOR, zorder=3)

        r = ax.bar(x=x-(w/2), height=portfolio['existing'], width=w, bottom=portfolio['new'], label="Existing", color=cls.DASHBOARD_EXISTING_FINDINGS_COLOR, zorder=3)
        ax.bar_label(r, padding=2, fontsize=6)

        r = ax.bar(x=x+(w/2), height=portfolio['resolved'], width=w, label="Resolved", color=cls.DASHBOARD_RESOLVED_FINDINGS_COLOR, zorder=3)
        ax.bar_label(r, padding=2, fontsize=6)

        max_val = np.max([np.max([xx+yy for xx,yy in zip(portfolio["new"], portfolio["existing"])]),np.max(portfolio["resolved"])])
        cls._format_image(ax=ax, x=x, columns=columns, max_value=max_val)

        return fig

class _AbstractSecurityDashboardResolutionTimesPlaceholder(_AbstractSecurityDashboardPlaceholder, ABC):
    LEGEND_ENTRIES_PER_SEVERITY = {
        "CRITICAL" : {'noRisk' : "at most 7 days", "lowRisk" : "between 7-14 days", "mediumRisk" : "between 14-30 days", "highRisk" : "at least 30 days"},
        "HIGH" : {'noRisk' : "at most 14 days", "lowRisk" : "between 14-30 days", "mediumRisk" : "between 30-180 days", "highRisk" : "at least 180 days"},
        "MEDIUM" : {'noRisk' : "at most 30 days", "lowRisk" : "between 30-180 days", "mediumRisk" : "between 180-365 days", "highRisk" : "at least 365 days"},
        "LOW" : {'noRisk' : "at most 180 days", "lowRisk" : "between 180-365 days", "mediumRisk" : "between 1-2 years", "highRisk" : "at least 2 years"}
    }
    DASHBOARD_RESOLUTION_LEGEND_COLORS = {
        'noRisk' : f"#{report_utils.pptx.DASHBOARD_RESOLUTION_NO_RISK_COLOR}",
        'lowRisk' : f"#{report_utils.pptx.DASHBOARD_RESOLUTION_LOW_RISK_COLOR}",
        'mediumRisk' : f"#{report_utils.pptx.DASHBOARD_RESOLUTION_MEDIUM_RISK_COLOR}",
        'highRisk' : f"#{report_utils.pptx.DASHBOARD_RESOLUTION_HIGH_RISK_COLOR}"
    }

    @classmethod
    def create_portfolio(cls):
        return cls.create_portfolio_helper(security_dashboard_resolution_times_portfolio_data, 'resolutionTimes', {"noRisk": 0, "lowRisk": 0, "mediumRisk": 0, "highRisk" : 0})

    @classmethod
    def create_dashboard_with_severity(cls, severity, width, height):
        portfolio_complete = cls.create_portfolio()
        portfolio = portfolio_complete[severity]
        columns = portfolio_complete['columns']
        legend_entries = cls.LEGEND_ENTRIES_PER_SEVERITY[severity]

        fig, ax = plt.subplots(figsize=(width,height), dpi=200, facecolor="none")
        bottom = np.zeros(len(columns))

        for entry, vals in portfolio.items():
            legend_entry = legend_entries[entry]
            np_vals = np.array(vals)
            r = ax.bar(x=columns, height=np_vals, label=legend_entry, bottom=bottom, color=cls.DASHBOARD_RESOLUTION_LEGEND_COLORS[entry], zorder=3)
            bottom += np_vals
        ax.bar_label(r, fontsize=6)

        x = np.arange(len(columns))
        max_val = np.max(np.sum(list(portfolio.values()), axis=0))
        cls._format_image(ax=ax, x=x, columns=columns, max_value=max_val)
        return fig


class SecurityDashboardCriticalFindingsPlaceholder(_AbstractSecurityDashboardFindingsPlaceholder):
    """Creates a portfolio bar chart depicting the number of new, existing, and resolved critical security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_CRITICAL_FINDINGS"

    @classmethod
    def value(cls, parameter=None):
        return cls.create_dashboard_with_severity(severity="CRITICAL", width=parameter['width'], height=parameter['height'])


class SecurityDashboardHighFindingsPlaceholder(_AbstractSecurityDashboardFindingsPlaceholder):
    """Creates a portfolio bar chart depicting the number of new, existing, and resolved high security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_HIGH_FINDINGS"

    @classmethod
    def value(cls, parameter=None):
        return cls.create_dashboard_with_severity(severity="HIGH", width=parameter['width'], height=parameter['height'])


class SecurityDashboardMediumFindingsPlaceholder(_AbstractSecurityDashboardFindingsPlaceholder):
    """Creates a portfolio bar chart depicting the number of new, existing, and resolved medium security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_MEDIUM_FINDINGS"

    @classmethod
    def value(cls, parameter=None):
        return cls.create_dashboard_with_severity(severity="MEDIUM", width=parameter['width'], height=parameter['height'])
    

class SecurityDashboardCriticalResolutionTimesPlaceholder(_AbstractSecurityDashboardResolutionTimesPlaceholder):
    """Creates a portfolio bar chart depicting the resolution times of critical security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_CRITICAL_RESOLUTION_TIMES"

    @classmethod
    def value(cls, parameter=None):
        return cls.create_dashboard_with_severity(severity="CRITICAL", width=parameter['width'], height=parameter['height'])
    

class SecurityDashboardHighResolutionTimesPlaceholder(_AbstractSecurityDashboardResolutionTimesPlaceholder):
    """Creates a portfolio bar chart depicting the resolution times of high security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_HIGH_RESOLUTION_TIMES"

    @classmethod
    def value(cls, parameter=None):
        return cls.create_dashboard_with_severity(severity="HIGH", width=parameter['width'], height=parameter['height'])
    

class SecurityDashboardMediumResolutionTimesPlaceholder(_AbstractSecurityDashboardResolutionTimesPlaceholder):
    """Creates a portfolio bar chart depicting the resolution times of medium security findings of the last 12 months (counting back from the <end_date>)"""

    key = "PORTFOLIO_PERIOD_SECURITY_DASHBOARD_MEDIUM_RESOLUTION_TIMES"

    @classmethod
    def value(cls, parameter=None):
        return cls.create_dashboard_with_severity(severity="MEDIUM", width=parameter['width'], height=parameter['height'])