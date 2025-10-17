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
from typing import Tuple
import plotly.graph_objs as go

from report_generator.generator import report_utils
from report_generator.generator.formatters import formatters
from report_generator.generator.data_models import maintainability_portfolio_data, security_ratings_portfolio_data, architecture_portfolio_data, osh_ratings_portfolio_data
from report_generator.generator.data_models import maintainability_delta_quality_new_code, maintainability_delta_quality_changed_code, maintainability_delta_quality_new_and_changed_code
import plotly.express as px
import logging
from .base import _AbstractImagePlaceholder


class _AbstractTreemapPlaceholder(_AbstractImagePlaceholder, ABC):
    @staticmethod
    def determine_rating_color(rating):
        return f"#{report_utils.pptx.determine_rating_color(rating)}"

    @staticmethod    
    def test_code_ratio_color(rating):
        return f"#{report_utils.pptx.test_code_ratio_color(rating)}"

    @staticmethod
    def interpolate_color(colors, t):
        return f"#{report_utils.pptx.interpolate_color(colors, t)}"
    
    @staticmethod
    def normalize_clamped(min_val, max_val, val):
        if min_val == max_val:
            return 0
        return max(0, min(1, (val - min_val) / (max_val - min_val)))


class _AbstractPortfolioTreemapPlaceholder(_AbstractTreemapPlaceholder, ABC):
    @staticmethod
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
    
    @staticmethod
    def create_blank_portfolio_treemap():
        names = []
        parents = []
        tracking = []

        portfolio = _AbstractPortfolioTreemapPlaceholder.create_portfolio()
        for s in portfolio.values():
            m = s['metadata']
            team_name = "Unset"
            if m['teamNames']:
                if len(m['teamNames']) > 1:
                    team_name = "Multiple teams"
                else:
                    team_name = m['teamNames'][0]
            if team_name not in names:
                names.append(team_name)
                parents.append("")
                tracking.append("")
            name = m['displayName']
            if name and name in names:
                name = f"{name} " # A workaround if, for example, a team name is the same as a system name
            elif not name:
                name = m['systemName']
            names.append(name)
            parents.append(team_name)
            tracking.append(m['systemName'])

        return {
            'names' : names,
            'parents' : parents,
            'tracking' : tracking
        }
    
    @staticmethod
    def create_treemap_values(portfolio, treemap_data):
        tracking = treemap_data.get("tracking", [])
        parents = treemap_data.get("parents", [])
        color_mapping = treemap_data.setdefault("color_mapping", {})

        values: list[int] = []
        for t, parent in zip(tracking, parents):
            if parent == "":
                values.append(0)
                color_mapping.setdefault(t, _AbstractPortfolioTreemapPlaceholder.BUNDLE_COLOR)
                continue

            end = portfolio.get(t, {}).get("end_date_data")
            value = 0 if not end else end.get("volumeInPersonMonths", 0)
            values.append(value)

        return values


    @staticmethod
    def create_treemap_figure(portfolio, treemap) -> go.Figure:
        treemap['values'] = _AbstractPortfolioTreemapPlaceholder.create_treemap_values(portfolio, treemap)
        fig = px.treemap(names=treemap['names'], parents=treemap['parents'], values=treemap['values'], color=treemap['color'], color_discrete_map=treemap['color_mapping'])
        fig.update_traces(root_color='rgba(250, 250, 250, 1)', textposition="middle center")
        return fig


    @staticmethod
    def prepare_portfolio_and_treemap() -> Tuple[dict,dict]:
        portfolio = _AbstractPortfolioTreemapPlaceholder.create_portfolio()
        treemap = _AbstractPortfolioTreemapPlaceholder.create_blank_portfolio_treemap()
        treemap['color'] = treemap['tracking']
        return portfolio, treemap


class EndDatePortfolioTreemapPlaceholder(_AbstractPortfolioTreemapPlaceholder, ABC):
    @staticmethod
    def create_end_date_portfolio_treemap(system_names, rating_func, determine_color_function):
        portfolio, treemap = _AbstractPortfolioTreemapPlaceholder.prepare_portfolio_and_treemap()
        treemap['color_mapping'] = dict.fromkeys(portfolio.keys(), _AbstractTreemapPlaceholder.NA_STAR_COLOR)
        for t in system_names:
            rating = rating_func(t)
            if rating is None:
                logging.debug(f"Cannot find end snapshot for {t}")
                continue
            if t not in treemap['color']:
                continue
            treemap['color_mapping'][t] = determine_color_function(rating) if rating is not None else _AbstractTreemapPlaceholder.NA_STAR_COLOR
            idx = treemap['color'].index(t)
            treemap['names'][idx] = f"{treemap['names'][idx].strip()}<br>{formatters.maintainability_round(rating)}"
        return _AbstractPortfolioTreemapPlaceholder.create_treemap_figure(portfolio, treemap)


class PeriodPortfolioTreemapPlaceholder(_AbstractPortfolioTreemapPlaceholder, ABC):
    @staticmethod
    def _calculate_differences(portfolio, metric):
        differences = {}
        for entry in portfolio.keys():
            if portfolio[entry]['start_date_data']['maintainabilityDate'] == portfolio[entry]['end_date_data']['maintainabilityDate'] or not portfolio[entry]['end_date_data'][metric] or not portfolio[entry]['start_date_data'][metric]:
                differences[entry] = None
            else:
                differences[entry] = portfolio[entry]['end_date_data'][metric]-portfolio[entry]['start_date_data'][metric]
        return differences
    

    @staticmethod
    def _create_color_mapping(differences, diff_min, diff_max, positive_color_range, negative_color_range):
        color_mapping = {}
        for entry in differences.keys():
            diff = differences[entry]
            if diff is None:
                color_mapping[entry] = _AbstractPortfolioTreemapPlaceholder.NA_STAR_COLOR
            elif diff < 0:
                t = _AbstractPortfolioTreemapPlaceholder.normalize_clamped(0, abs(diff_min), abs(diff))
                color_mapping[entry] = _AbstractTreemapPlaceholder.interpolate_color(negative_color_range, t)
            else:
                t = _AbstractPortfolioTreemapPlaceholder.normalize_clamped(0, diff_max, diff)
                color_mapping[entry] = _AbstractTreemapPlaceholder.interpolate_color(positive_color_range, t)
        return color_mapping
        

    @staticmethod
    def create_period_portfolio_treemap(metric, positive_color_range, negative_color_range):
        portfolio, treemap = _AbstractPortfolioTreemapPlaceholder.prepare_portfolio_and_treemap()
        differences = PeriodPortfolioTreemapPlaceholder._calculate_differences(portfolio, metric)
        processed_vals = [x for x in differences.values() if x is not None]
        treemap['color_mapping'] = PeriodPortfolioTreemapPlaceholder._create_color_mapping(differences, min(processed_vals), max(processed_vals),
                                                                                           positive_color_range, negative_color_range)
        for system_name in portfolio.keys():
            if system_name not in treemap['color']:
                continue
            idx = treemap['color'].index(system_name)
            treemap['names'][idx] = f"{treemap['names'][idx].strip()}<br>{round(differences[system_name], 2) if differences[system_name] else "N/A"}"
        return _AbstractPortfolioTreemapPlaceholder.create_treemap_figure(portfolio, treemap)

    
class MaintainabilityPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the maintainability rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY"

    @classmethod
    def value(cls, param=None):
        portfolio, _ = _AbstractPortfolioTreemapPlaceholder.prepare_portfolio_and_treemap()
        f = lambda t: portfolio[t]['end_date_data']['maintainability']
        return cls.create_end_date_portfolio_treemap(portfolio.keys(), f, cls.determine_rating_color)

    
class MaintainabilityChangePortfolioTreemapPlaceholder(PeriodPortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the change in maintainability rating of the individual systems during the specified period."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_CHANGE"

    @classmethod
    def value(cls, param=None):
        return cls.create_period_portfolio_treemap('maintainability', report_utils.pptx.MAINTAINABILITY_POS_CHANGE_RANGE_COLORS, report_utils.pptx.MAINTAINABILITY_NEG_CHANGE_RANGE_COLORS)


class VolumeChangePortfolioTreemapPlaceholder(PeriodPortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the change in volume change (effort) of the individual systems during the specified period."""

    key = "PORTFOLIO_PERIOD_VOLUME_CHANGE"

    @classmethod
    def value(cls, param=None):
        return cls.create_period_portfolio_treemap('volumeInPersonMonths', report_utils.pptx.VOLUME_POS_CHANGE_RANGE_COLORS, report_utils.pptx.VOLUME_NEG_CHANGE_RANGE_COLORS)
    

class TestCodePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the test-to-production code ratio of the individual systems."""

    key = "PORTFOLIO_PERIOD_TEST_CODE"

    @classmethod
    def value(cls, param=None):
        portfolio, _ = _AbstractPortfolioTreemapPlaceholder.prepare_portfolio_and_treemap()
        f = lambda t: portfolio[t]['end_date_data']['testCodeRatio']
        return cls.create_end_date_portfolio_treemap(portfolio.keys(), f, cls.test_code_ratio_color)


class TestCodeChangePortfolioTreemapPlaceholder(PeriodPortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the change in test code volume change (%) of the individual systems during the specified period."""

    key = "PORTFOLIO_PERIOD_TEST_CODE_CHANGE"

    @classmethod
    def value(cls, param=None):
        return cls.create_period_portfolio_treemap('testCodeRatio', report_utils.pptx.MAINTAINABILITY_POS_CHANGE_RANGE_COLORS, report_utils.pptx.MAINTAINABILITY_NEG_CHANGE_RANGE_COLORS)
    
    
class SecurityRatingsPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the security rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_SECURITY_RATINGS"

    @classmethod
    def value(cls, param=None):
        f = lambda t: security_ratings_portfolio_data.end_snapshot(t)['rating'] if security_ratings_portfolio_data.end_snapshot(t) else 0
        return cls.create_end_date_portfolio_treemap(security_ratings_portfolio_data.system_names, f, cls.determine_rating_color)


class ArchitecturePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the architecture quality rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_ARCHITECTURE"

    @classmethod
    def value(cls, param=None):
        f = lambda t: architecture_portfolio_data.end_snapshot(t)['ratings']['architecture'] if architecture_portfolio_data.end_snapshot(t) else 0
        return cls.create_end_date_portfolio_treemap(architecture_portfolio_data.system_names, f, cls.determine_rating_color)
    

class MaintainabilityDeltaQualityNewCodePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the delta quality of maintainability rating (new code) of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_DELTA_QUALITY_NEW_CODE"

    @classmethod
    def value(cls, param=None):
        f = lambda t: maintainability_delta_quality_new_code.data[t]['filesRatingAtEnd'] if maintainability_delta_quality_new_code.data[t] else 0
        return cls.create_end_date_portfolio_treemap(maintainability_delta_quality_new_code.system_names, f, cls.determine_rating_color)
    

class MaintainabilityDeltaQualityChangedCodePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the delta quality of maintainability rating (changed code) of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_DELTA_QUALITY_CHANGED_CODE"

    @classmethod
    def value(cls, param=None):
        f = lambda t: maintainability_delta_quality_changed_code.data[t]['filesRatingAtEnd'] if maintainability_delta_quality_changed_code.data[t] else 0
        return cls.create_end_date_portfolio_treemap(maintainability_delta_quality_changed_code.system_names, f, cls.determine_rating_color)
    

class MaintainabilityDeltaQualityNewAndChangedCodePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the delta quality of maintainability rating (new and changed code) of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_DELTA_QUALITY_NEW_AND_CHANGED_CODE"

    @classmethod
    def value(cls, param=None):
        f = lambda t: maintainability_delta_quality_new_and_changed_code.data[t]['filesRatingAtEnd'] if maintainability_delta_quality_new_and_changed_code.data[t] else 0
        return cls.create_end_date_portfolio_treemap(maintainability_delta_quality_new_and_changed_code.system_names, f, cls.determine_rating_color)
    
    
class OSHRatingsPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the open-source health rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_OSH_RATINGS"

    @classmethod
    def value(cls, param=None):
        def rating_function(system_name):
            system = osh_ratings_portfolio_data.find_system(system_name)
            props = system.get("sbom", {}).get("metadata", {}).get("properties", [])
            return next(
                (float(p["value"]) for p in props if p["name"] == "sigrid:ratings:system"),
                0.0
            )
        return cls.create_end_date_portfolio_treemap(osh_ratings_portfolio_data.system_names, rating_function, cls.determine_rating_color)