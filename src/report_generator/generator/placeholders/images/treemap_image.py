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
from typing import Tuple, ClassVar, Dict, Callable
import logging

from report_generator.generator import report_utils
from report_generator.generator.formatters import formatters
from report_generator.generator.data_models import maintainability_portfolio_data, security_ratings_portfolio_data, architecture_portfolio_data, osh_ratings_portfolio_data
from report_generator.generator.data_models import maintainability_delta_quality_new_code, maintainability_delta_quality_changed_code, maintainability_delta_quality_new_and_changed_code
from report_generator.generator.placeholders.images.base import _AbstractImagePlaceholder

import pandas as pd
import matplotlib.pyplot as plt
import mpl_extra.treemap as tr

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
    grouping_processors: ClassVar[Dict[str, Callable]] = {}

    @staticmethod
    def create_portfolio():
        res = {}
        system_names = maintainability_portfolio_data.system_names
        for system_name in system_names:
            md = maintainability_portfolio_data.get_system_metadata(system_name)
            if not md['active'] or md['isDevelopmentOnly']:
                continue

            res[system_name] = {
                'metadata' : md,
                'start_date_data' : maintainability_portfolio_data.start_snapshot(system_name),
                'end_date_data' : maintainability_portfolio_data.end_snapshot(system_name)
            }
        return res


    @staticmethod
    def _process_team_grouping(metadata):
        team_name = "Unset"
        if metadata['teamNames']:
            if len(metadata['teamNames']) > 1:
                team_name = "Multiple teams"
            else:
                team_name = metadata['teamNames'][0]
        return team_name
    

    @staticmethod
    def _process_lifecycle_grouping(metadata):
        if metadata['lifecyclePhase']:
            return report_utils.common.METADATA_LIFECYCLE_MAPPING[metadata['lifecyclePhase']]
        return "Unset"
    

    _grouping_processors = {
        'team' : _process_team_grouping.__func__,
        'lifecycle' : _process_lifecycle_grouping.__func__
    }
    

    @classmethod
    def _create_blank_portfolio_and_treemap(cls) -> Tuple[dict,dict]:
        global _grouping

        system_names = []
        display_names = []
        root_names = []

        _grouping = 'lifecycle' # TODO

        portfolio = cls.create_portfolio()
        for s in portfolio.values():
            m = s['metadata']

            root_name = _AbstractPortfolioTreemapPlaceholder._grouping_processors[_grouping](m)
            display_name = m['displayName']
            if display_name and display_name in display_names:
                display_name = f"{display_name} " # A workaround if, for example, a team name is the same as a system name
            elif not display_name:
                display_name = m['systemName']
            display_names.append(display_name)
            root_names.append(root_name)
            system_names.append(m['systemName'])

        treemap = {
            'display_names' : display_names,
            'root_names' : root_names,
            'system_names' : system_names,
            'color_mapping' : {},
            'volumes' : []
        }
        return portfolio, treemap


    @staticmethod
    def create_treemap_values(portfolio, treemap_data) -> list[float]:
        values: list[float] = []
        for system_name in treemap_data["system_names"]:
            end = portfolio.get(system_name, {}).get("end_date_data")
            value = 1e-6 if not end else end.get("volumeInPersonMonths", 1e-6)
            values.append(max(value,1e-6))
        return values


    @staticmethod
    def create_treemap_figure_data(treemap):
        return {
            'labels' : treemap['display_names'],
            'system_names' : treemap['system_names'],
            'roots' : treemap['root_names'],
            'volumes' : treemap['volumes'],
            'color_names' : treemap['system_names'],
            'color_mapping' : treemap['color_mapping'],
            'figure_type': 'treemap'
        }
    

    @staticmethod
    def _sanitize_treemap(treemap):
        root_names = list(set(treemap['root_names']))
        portfolio_volume = sum(treemap['volumes'])

        volume_per_root = dict.fromkeys(root_names, 0)
        for volume, root in zip(treemap["volumes"], treemap["root_names"]):
            volume_per_root[root] += volume

        # Keep only entries where the team has at least 1% of total volume
        threshold = 0.01 * portfolio_volume
        keep_indices = [i for i, root in enumerate(treemap["root_names"]) if volume_per_root[root] >= threshold]
        
        for key in ["volumes", "root_names", "display_names", "system_names"]:
            treemap[key] = [treemap[key][i] for i in keep_indices]

    
    @classmethod
    def prepare_portfolio_and_treemap(cls) -> Tuple[dict,dict]:
        portfolio, treemap = cls._create_blank_portfolio_and_treemap()
        treemap['volumes'] = cls.create_treemap_values(portfolio, treemap)
        cls._sanitize_treemap(treemap)
        return portfolio, treemap

    @classmethod
    def draw_image(cls, width, height, fig_data):
        if width <= 0 or height <= 0:
            logging.error("Width and/or height is <0.")
            return None
        if fig_data is None:
            logging.error("Figure data is None.")
            return
        fig, ax = plt.subplots(figsize=(width,height), dpi=200)
        subkeys = ["system_names", "volumes", "labels", "roots"]
        df = pd.DataFrame({k: fig_data[k] for k in subkeys})
        tr.treemap(axes=ax, data=df, area="volumes", levels=["roots", "system_names"], top=True,
                fill="system_names", cmap=fig_data['color_mapping'], labels="labels",
                rectprops={'ec':'w', 'pad':(0,0,0,2)},
                textprops={
                    'fontfamily':'sans-serif', 'reflow':True, 'place':'center', 'grow':True,
                    'max_fontsize':4, 'color':'k', 'pady':1, 'padx':1}, # Text inside squares
                subgroup_rectprops={'roots':{'ec':'w', 'fc':cls.BUNDLE_COLOR}},
                subgroup_textprops={'roots':{'place':'top center', 'max_fontsize':3, 'pady':1, 'fontfamily':'sans-serif', 'color':'k'}}
        )
        ax.axis("off")
        return fig


class EndDatePortfolioTreemapPlaceholder(_AbstractPortfolioTreemapPlaceholder, ABC):
    @classmethod
    def create_end_date_portfolio_treemap(cls, rating_func, rating_rounding_func, determine_color_function):
        portfolio, treemap = cls.prepare_portfolio_and_treemap()
        treemap['color_mapping'] = dict.fromkeys(portfolio.keys(), cls.NA_STAR_COLOR)
        for t in treemap['system_names']:
            rating = rating_func(t)
            if rating is None:
                logging.debug(f"Cannot find end snapshot for {t}")
                continue
            treemap['color_mapping'][t] = determine_color_function(rating) if rating is not None else cls.NA_STAR_COLOR
            idx = treemap['system_names'].index(t)
            treemap['display_names'][idx] = f"{treemap['display_names'][idx].strip()}\n{rating_rounding_func(rating)}"
        return cls.create_treemap_figure_data(treemap)


class PeriodPortfolioTreemapPlaceholder(_AbstractPortfolioTreemapPlaceholder, ABC):
    @staticmethod
    def _calculate_differences(portfolio, metric, system_names):
        differences = {}
        for system_name in system_names:
            entry = portfolio.get(system_name)
            if not entry:
                continue

            if entry['start_date_data']['maintainabilityDate'] == entry['end_date_data']['maintainabilityDate'] or not entry['end_date_data'][metric] or not entry['start_date_data'][metric]:
                differences[system_name] = None
            else:
                differences[system_name] = entry['end_date_data'][metric]-entry['start_date_data'][metric]

        return differences
    

    @classmethod
    def _create_color_mapping(cls, differences, diff_min, diff_max, positive_color_range, negative_color_range, system_names):
        color_mapping = {}
        for system_name in system_names:
            diff = differences.get(system_name, None)
            value = None
            if diff is None:
                value = cls.NA_STAR_COLOR
            elif diff < 0:
                t = cls.normalize_clamped(0, abs(diff_min), abs(diff))
                value = cls.interpolate_color(negative_color_range, t)
            else:
                t = cls.normalize_clamped(0, diff_max, diff)
                value = cls.interpolate_color(positive_color_range, t)
            color_mapping[system_name] = value

        return color_mapping
    
    @staticmethod
    def _get_and_format_difference(differences, system_name, is_percentage):
        diff = differences.get(system_name)
        if diff is not None:
            return round(diff, 2) if not is_percentage else formatters.ratio_to_percentage(diff)
        return "N/A"

    @classmethod
    def create_period_portfolio_treemap(cls, metric, positive_color_range, negative_color_range, is_percentage=False):
        portfolio, treemap = cls.prepare_portfolio_and_treemap()
        differences = cls._calculate_differences(portfolio, metric, treemap['system_names'])
        processed_vals = [x for x in differences.values() if x is not None]
        if len(processed_vals) == 0:
            return None
        treemap['color_mapping'] = cls._create_color_mapping(differences, min(processed_vals), max(processed_vals),
                                                                                           positive_color_range, negative_color_range, treemap['system_names'])
        for system_name in treemap['system_names']:
            idx = treemap['system_names'].index(system_name)
            treemap['display_names'][idx] = f"{treemap['display_names'][idx].strip()}\n{cls._get_and_format_difference(differences, system_name, is_percentage)}"
        return cls.create_treemap_figure_data(treemap)

    
class MaintainabilityPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the maintainability rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY"

    @classmethod
    def value(cls, parameter=None):
        portfolio = cls.create_portfolio()
        f = lambda t: portfolio.get(t, {}).get('end_date_data', {}).get('maintainability', None)
        fig_data = cls.create_end_date_portfolio_treemap(rating_func=f, rating_rounding_func=formatters.maintainability_round, determine_color_function=cls.determine_rating_color)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)

    
class MaintainabilityChangePortfolioTreemapPlaceholder(PeriodPortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the change in maintainability rating of the individual systems during the specified period."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_CHANGE"

    @classmethod
    def value(cls, parameter=None):
        fig_data = cls.create_period_portfolio_treemap(metric='maintainability', positive_color_range=report_utils.pptx.MAINTAINABILITY_POS_CHANGE_RANGE_COLORS,
                                                   negative_color_range=report_utils.pptx.MAINTAINABILITY_NEG_CHANGE_RANGE_COLORS)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)


class VolumeChangePortfolioTreemapPlaceholder(PeriodPortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the change in volume change (effort) of the individual systems during the specified period."""

    key = "PORTFOLIO_PERIOD_VOLUME_CHANGE"

    @classmethod
    def value(cls, parameter=None):
        fig_data = cls.create_period_portfolio_treemap(metric='volumeInPersonMonths', positive_color_range=report_utils.pptx.VOLUME_POS_CHANGE_RANGE_COLORS,
                                                   negative_color_range=report_utils.pptx.VOLUME_NEG_CHANGE_RANGE_COLORS)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)
    

class TestCodePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the test-to-production code ratio of the individual systems."""

    key = "PORTFOLIO_PERIOD_TEST_CODE"

    @classmethod
    def value(cls, parameter=None):
        portfolio = cls.create_portfolio()
        f = lambda t: portfolio[t]['end_date_data']['testCodeRatio']
        fig_data = cls.create_end_date_portfolio_treemap(rating_func=f, rating_rounding_func=formatters.ratio_to_percentage, determine_color_function=cls.test_code_ratio_color)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)


class TestCodeChangePortfolioTreemapPlaceholder(PeriodPortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the change in test code volume change (%) of the individual systems during the specified period."""

    key = "PORTFOLIO_PERIOD_TEST_CODE_CHANGE"

    @classmethod
    def value(cls, parameter=None):
        fig_data = cls.create_period_portfolio_treemap(metric='testCodeRatio', positive_color_range=report_utils.pptx.MAINTAINABILITY_POS_CHANGE_RANGE_COLORS,
                                                   negative_color_range=report_utils.pptx.MAINTAINABILITY_NEG_CHANGE_RANGE_COLORS, is_percentage=True)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)
    
    
class SecurityRatingsPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the security rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_SECURITY_RATINGS"

    @classmethod
    def value(cls, parameter=None):
        f = lambda t: security_ratings_portfolio_data.end_snapshot(t)['rating'] if security_ratings_portfolio_data.end_snapshot(t) else 0
        fig_data = cls.create_end_date_portfolio_treemap(rating_func=f, rating_rounding_func=formatters.maintainability_round, determine_color_function=cls.determine_rating_color)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)


class ArchitecturePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the architecture quality rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_ARCHITECTURE"

    @classmethod
    def value(cls, parameter=None):
        f = lambda t: architecture_portfolio_data.end_snapshot(t)['ratings']['architecture'] if architecture_portfolio_data.end_snapshot(t) else 0
        fig_data = cls.create_end_date_portfolio_treemap(rating_func=f, rating_rounding_func=formatters.maintainability_round, determine_color_function=cls.determine_rating_color)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)
    

class MaintainabilityDeltaQualityNewCodePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the delta quality of maintainability rating (new code) of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_DELTA_QUALITY_NEW_CODE"

    @classmethod
    def value(cls, parameter=None):
        f = lambda t: maintainability_delta_quality_new_code.data[t]['filesRatingAtEnd'] if maintainability_delta_quality_new_code.data[t] and maintainability_delta_quality_new_code.data[t]['filesRatingAtEnd'] else 0
        fig_data = cls.create_end_date_portfolio_treemap(rating_func=f, rating_rounding_func=formatters.maintainability_round, determine_color_function=cls.determine_rating_color)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)
    

class MaintainabilityDeltaQualityChangedCodePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the delta quality of maintainability rating (changed code) of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_DELTA_QUALITY_CHANGED_CODE"

    @classmethod
    def value(cls, parameter=None):
        f = lambda t: maintainability_delta_quality_changed_code.data[t]['filesRatingAtEnd'] if maintainability_delta_quality_changed_code.data[t] and maintainability_delta_quality_changed_code.data[t]['filesRatingAtEnd'] else 0
        fig_data = cls.create_end_date_portfolio_treemap(rating_func=f, rating_rounding_func=formatters.maintainability_round, determine_color_function=cls.determine_rating_color)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)
    

class MaintainabilityDeltaQualityNewAndChangedCodePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the delta quality of maintainability rating (new and changed code) of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_DELTA_QUALITY_NEW_AND_CHANGED_CODE"

    @classmethod
    def value(cls, parameter=None):
        f = lambda t: maintainability_delta_quality_new_and_changed_code.data[t]['filesRatingAtEnd'] if maintainability_delta_quality_new_and_changed_code.data[t] and maintainability_delta_quality_new_and_changed_code.data[t]['filesRatingAtEnd'] else 0
        fig_data = cls.create_end_date_portfolio_treemap(rating_func=f, rating_rounding_func=formatters.maintainability_round, determine_color_function=cls.determine_rating_color)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)
    
    
class OSHRatingsPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the open-source health rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_OSH_RATINGS"

    @classmethod
    def value(cls, parameter=None):
        def rating_function(system_name):
            system = osh_ratings_portfolio_data.find_system(system_name)
            props = system.get("sbom", {}).get("metadata", {}).get("properties", [])
            return next((float(p["value"]) for p in props if p["name"] == "sigrid:ratings:system"),0.0)
        fig_data = cls.create_end_date_portfolio_treemap(rating_func=rating_function, rating_rounding_func=formatters.maintainability_round, determine_color_function=cls.determine_rating_color)
        return cls.draw_image(width=parameter['width'], height=parameter['height'], fig_data=fig_data)