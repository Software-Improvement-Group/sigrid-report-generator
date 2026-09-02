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

from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import pytest

from report_generator.generator.placeholders import context as placeholders_context
from report_generator.generator.placeholders.implementations.images.treemaps.utils.treemap._autofit_text import (
    _DEFAULT_LINESPACING,
    AutofitText,
)

plt.switch_backend("Agg")


@pytest.fixture(autouse=True)
def reset_grouping_context():
    placeholders_context.reset_group_by()
    yield
    placeholders_context.reset_group_by()


class TestAutofitText:
    """Regression tests that exercise the real matplotlib draw path."""

    def _draw(self, **kwargs):
        fig, ax = plt.subplots()
        ax.axis("off")  # matches production; also avoids unrelated tick-draw machinery
        try:
            text = AutofitText((0.5, 0.5), 0.4, 0.2, text="Some System Name", **kwargs)
            ax.add_artist(text)
            fig.canvas.draw()
        finally:
            plt.close(fig)

    def test_draw_with_reflow_succeeds(self):
        """Reflow path must not choke on matplotlib's 'normal' linespacing default."""
        # Would raise ValueError: could not convert string to float: 'normal'
        # on matplotlib >= 3.11 before the fix.
        self._draw(reflow=True, ha="center", va="center")

    def test_draw_without_reflow_succeeds(self):
        self._draw(ha="center", va="center")

    def test_numeric_linespacing_defaults_when_non_numeric(self):
        text = AutofitText((0, 0), 1, 1, text="x")
        text._linespacing = "normal"
        assert text._numeric_linespacing() == pytest.approx(_DEFAULT_LINESPACING)

    def test_numeric_linespacing_preserves_explicit_value(self):
        text = AutofitText((0, 0), 1, 1, text="x", linespacing=1.5)
        assert text._numeric_linespacing() == pytest.approx(1.5)


class TestTreemapImagePlaceholder:
    """Test cases for treemap image generation with empty data handling."""

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.tr"
    )
    def test_draw_image_with_empty_dataframe_returns_none(self, mock_treemap, mock_plt):
        """Test that draw_image returns None when dataframe is empty."""
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        # Mock figure and axes
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        # Create empty fig_data
        fig_data = {
            "system_names": [],
            "volumes": [],
            "labels": [],
            "root_names": [],
            "color_mapping": {},
        }

        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, fig_data)

        assert result is None
        mock_plt.close.assert_called_once_with(mock_fig)
        # Treemap should not be called with empty data
        mock_treemap.treemap.assert_not_called()

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.tr"
    )
    def test_draw_image_with_empty_color_mapping_creates_default(
        self, mock_treemap, mock_plt
    ):
        """Test that draw_image creates default color mapping when empty."""
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        # Mock figure and axes
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        # Create fig_data with systems but empty color_mapping
        fig_data = {
            "system_names": ["system1", "system2"],
            "volumes": [100, 200],
            "labels": ["System 1", "System 2"],
            "root_names": ["root", "root"],
            "color_mapping": {},
        }

        _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, fig_data)

        # Should have built a TreemapStyle with a non-empty color mapping
        assert mock_treemap.treemap.called
        style_kwargs = mock_treemap.TreemapStyle.call_args[1]
        assert "cmap" in style_kwargs
        assert len(style_kwargs["cmap"]) == 2  # Should have colors for both systems
        assert "system1" in style_kwargs["cmap"]
        assert "system2" in style_kwargs["cmap"]

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.tr"
    )
    def test_draw_image_with_invalid_dimensions_returns_none(
        self, mock_treemap, mock_plt
    ):
        """Test that draw_image returns None with invalid dimensions."""
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        fig_data = {
            "system_names": ["system1"],
            "volumes": [100],
            "labels": ["System 1"],
            "root_names": ["root"],
            "color_mapping": {"system1": "#FF0000"},
        }

        # Test with zero width
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(0, 10, fig_data)
        assert result is None

        # Test with negative height
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, -5, fig_data)
        assert result is None

        # Test with both invalid
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(-1, 0, fig_data)
        assert result is None

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.plt"
    )
    def test_draw_image_with_none_fig_data_returns_none(self, mock_plt):
        """Test that draw_image returns None when fig_data is None."""
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, None)
        assert result is None

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.tr"
    )
    def test_draw_image_with_valid_data_creates_treemap(self, mock_treemap, mock_plt):
        """Test that draw_image creates treemap with valid data and color mapping."""
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        # Mock figure and axes
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        # Create valid fig_data
        fig_data = {
            "system_names": ["system1", "system2"],
            "volumes": [100, 200],
            "labels": ["System 1", "System 2"],
            "root_names": ["root", "root"],
            "color_mapping": {"system1": "#FF0000", "system2": "#00FF00"},
        }

        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, fig_data)

        # Should return the figure
        assert result == mock_fig
        # TreemapStyle should be built with the provided color mapping
        mock_treemap.treemap.assert_called_once()
        columns_kwargs = mock_treemap.PlotColumns.call_args[1]
        style_kwargs = mock_treemap.TreemapStyle.call_args[1]
        assert style_kwargs["cmap"] == fig_data["color_mapping"]
        # A single non-"Unset" group should still show its grouping header
        assert columns_kwargs["levels"] == ["root_names", "system_names"]
        assert style_kwargs["subgroup_rectprops"]
        # Axes should be turned off
        mock_ax.axis.assert_called_once_with("off")

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.tr"
    )
    def test_draw_image_hides_grouping_header_when_only_unset(
        self, mock_treemap, mock_plt
    ):
        """The grey grouping header bar must not be shown when every system's group is 'Unset'."""
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        fig_data = {
            "system_names": ["system1", "system2"],
            "volumes": [100, 200],
            "labels": ["System 1", "System 2"],
            "root_names": ["Unset", "Unset"],
            "color_mapping": {"system1": "#FF0000", "system2": "#00FF00"},
        }

        _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, fig_data)

        columns_kwargs = mock_treemap.PlotColumns.call_args[1]
        style_kwargs = mock_treemap.TreemapStyle.call_args[1]
        assert columns_kwargs["levels"] == ["system_names"]
        assert not style_kwargs["subgroup_rectprops"]
        assert not style_kwargs["subgroup_textprops"]

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.tr"
    )
    def test_draw_image_shows_grouping_header_when_unset_mixed_with_other_groups(
        self, mock_treemap, mock_plt
    ):
        """When 'Unset' is only one of several distinct groups, the header must still show."""
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        fig_data = {
            "system_names": ["system1", "system2"],
            "volumes": [100, 200],
            "labels": ["System 1", "System 2"],
            "root_names": ["Unset", "Team A"],
            "color_mapping": {"system1": "#FF0000", "system2": "#00FF00"},
        }

        _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, fig_data)

        columns_kwargs = mock_treemap.PlotColumns.call_args[1]
        style_kwargs = mock_treemap.TreemapStyle.call_args[1]
        assert columns_kwargs["levels"] == ["root_names", "system_names"]
        assert style_kwargs["subgroup_rectprops"]
        assert style_kwargs["subgroup_textprops"]


class TestMainTechnologyGrouping:
    """Test cases for the 'main_technology' treemap grouping processor."""

    def test_main_technology_available_as_parameter(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        assert "main_technology" in (
            _AbstractPortfolioTreemapPlaceholder.grouping_processors
        )
        assert (
            "_GROUPED_BY_MAIN_TECHNOLOGY"
            in _AbstractPortfolioTreemapPlaceholder.GROUPING_PARAMETERS
        )

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemaps.treemap_base.get_technology_name"
    )
    def test_grouping_returns_readable_technology_name(self, mock_get_name):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        mock_get_name.return_value = "Java"
        result = _AbstractPortfolioTreemapPlaceholder._process_main_technology_grouping(
            {"mainTechnology": "java"}
        )

        assert result == "Java"
        mock_get_name.assert_called_once_with("java")

    def test_grouping_returns_unset_when_missing(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        assert (
            _AbstractPortfolioTreemapPlaceholder._process_main_technology_grouping(
                {"mainTechnology": None}
            )
            == "Unset"
        )
        assert (
            _AbstractPortfolioTreemapPlaceholder._process_main_technology_grouping(
                {"mainTechnology": ""}
            )
            == "Unset"
        )


class TestNewGroupingProcessors:
    """Test cases for the grouping processors added for the 6 previously-unsupported
    filter dimensions."""

    def test_all_eleven_dimensions_registered(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        assert set(_AbstractPortfolioTreemapPlaceholder.grouping_processors.keys()) == {
            "team",
            "division",
            "lifecycle",
            "business_criticality",
            "deployment",
            "distribution",
            "application_type",
            "target_industry",
            "technology_category",
            "main_technology",
            "supplier",
        }

    def test_division_grouping(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        p = _AbstractPortfolioTreemapPlaceholder
        assert p._process_division_grouping({"divisionName": "Finance"}) == "Finance"
        assert p._process_division_grouping({"divisionName": None}) == "Unset"

    def test_distribution_grouping(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        p = _AbstractPortfolioTreemapPlaceholder
        assert (
            p._process_distribution_grouping(
                {"softwareDistributionStrategy": "NETWORK_SERVICE"}
            )
            == "Network service"
        )
        assert (
            p._process_distribution_grouping({"softwareDistributionStrategy": None})
            == "Unset"
        )

    def test_application_type_grouping(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        p = _AbstractPortfolioTreemapPlaceholder
        assert (
            p._process_application_type_grouping({"applicationType": "ANALYTICAL"})
            == "Analytical"
        )
        assert (
            p._process_application_type_grouping({"applicationType": None}) == "Unset"
        )

    def test_target_industry_grouping(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        p = _AbstractPortfolioTreemapPlaceholder
        assert (
            p._process_target_industry_grouping({"targetIndustry": "ICD8300"})
            == "Banking"
        )
        assert p._process_target_industry_grouping({"targetIndustry": None}) == "Unset"

    def test_technology_category_grouping(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        p = _AbstractPortfolioTreemapPlaceholder
        assert (
            p._process_technology_category_grouping({"technologyCategory": "MAINFRAME"})
            == "Mainframe"
        )
        assert (
            p._process_technology_category_grouping({"technologyCategory": None})
            == "Unset"
        )

    def test_supplier_grouping(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        p = _AbstractPortfolioTreemapPlaceholder
        assert p._process_supplier_grouping({"supplierNames": ["Acme"]}) == "Acme"
        assert (
            p._process_supplier_grouping({"supplierNames": ["Acme", "Globex"]})
            == "Multiple suppliers"
        )
        assert p._process_supplier_grouping({"supplierNames": []}) == "Unset"

    def test_team_grouping_still_behaves_as_before(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        p = _AbstractPortfolioTreemapPlaceholder
        assert p._process_team_grouping({"teamNames": ["TeamA"]}) == "TeamA"
        assert (
            p._process_team_grouping({"teamNames": ["TeamA", "TeamB"]})
            == "Multiple teams"
        )
        assert p._process_team_grouping({"teamNames": []}) == "Unset"


def _fake_shape(text):
    shape = MagicMock()
    shape.has_text_frame = True
    shape.text_frame.paragraphs = [MagicMock(text=text)]
    shape.shape_type = None  # never MSO_SHAPE_TYPE.GROUP
    shape.width.inches = 1.0
    shape.height.inches = 1.0
    return shape


def _fake_report(*texts):
    report = MagicMock()
    report.type = "PRESENTATION"
    slide = MagicMock()
    slide.shapes = [_fake_shape(text) for text in texts]
    report.slides = [slide]
    return report


class TestDimensionFromParameter:
    """Grouping is a plain parameter value now: the full "_GROUPED_BY_X" suffix,
    or "" for the bare key. _dimension_from_parameter translates either form back
    into the lowercase dimension name grouping_processors expects."""

    def test_bare_parameter_uses_group_by_context(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        placeholders_context.set_group_by("lifecycle")

        assert (
            _AbstractPortfolioTreemapPlaceholder._dimension_from_parameter("")
            == "lifecycle"
        )

    def test_suffixed_parameter_strips_marker(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        assert (
            _AbstractPortfolioTreemapPlaceholder._dimension_from_parameter(
                "_GROUPED_BY_MAIN_TECHNOLOGY"
            )
            == "main_technology"
        )


class TestResolveGroupingVariants:
    """Grouping is resolved through the normal ParameterizedPlaceholder mechanism:
    one key template with a single {parameter} token, substituted with either ""
    (the bare, suffix-free default that follows --group-by) or one of the
    "_GROUPED_BY_X" suffixes (pinned to dimension X). No custom resolve()."""

    def test_key_uses_a_single_parameter_token(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.maintainability_treemap import (
            MaintainabilityPortfolioTreemapPlaceholder,
        )

        assert (
            MaintainabilityPortfolioTreemapPlaceholder.key
            == "PORTFOLIO_PERIOD_MAINTAINABILITY{parameter}"
        )

    def test_resolve_only_calls_value_for_keys_present_in_the_report(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.maintainability_treemap import (
            MaintainabilityPortfolioTreemapPlaceholder as Placeholder,
        )

        report = _fake_report(
            "PORTFOLIO_PERIOD_MAINTAINABILITY",
            "PORTFOLIO_PERIOD_MAINTAINABILITY_GROUPED_BY_MAIN_TECHNOLOGY",
        )

        with (
            patch.object(
                Placeholder, "_determine_resolve_method", return_value="resolve_pptx"
            ),
            patch.object(Placeholder, "value", return_value=None) as mock_value,
        ):
            Placeholder.resolve(report)

        resolved_parameters = {c.args[0] for c in mock_value.call_args_list}
        assert resolved_parameters == {"", "_GROUPED_BY_MAIN_TECHNOLOGY"}

    def test_resolve_bare_key_uses_group_by_context(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.maintainability_treemap import (
            MaintainabilityPortfolioTreemapPlaceholder as Placeholder,
        )

        placeholders_context.set_group_by("lifecycle")
        report = _fake_report("PORTFOLIO_PERIOD_MAINTAINABILITY")

        with (
            patch.object(
                Placeholder, "_determine_resolve_method", return_value="resolve_pptx"
            ),
            patch.object(Placeholder, "value", return_value=None) as mock_value,
        ):
            Placeholder.resolve(report)

        mock_value.assert_called_once_with("")
        assert Placeholder._dimension_from_parameter("") == "lifecycle"

    def test_resolve_pinned_key_ignores_group_by_context(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.maintainability_treemap import (
            MaintainabilityPortfolioTreemapPlaceholder as Placeholder,
        )

        placeholders_context.set_group_by("lifecycle")
        report = _fake_report(
            "PORTFOLIO_PERIOD_MAINTAINABILITY_GROUPED_BY_MAIN_TECHNOLOGY"
        )

        with (
            patch.object(
                Placeholder, "_determine_resolve_method", return_value="resolve_pptx"
            ),
            patch.object(Placeholder, "value", return_value=None) as mock_value,
        ):
            Placeholder.resolve(report)

        mock_value.assert_called_once_with("_GROUPED_BY_MAIN_TECHNOLOGY")
        assert (
            Placeholder._dimension_from_parameter("_GROUPED_BY_MAIN_TECHNOLOGY")
            == "main_technology"
        )

    def test_resolve_ignores_unrelated_key_sharing_prefix(self):
        """PORTFOLIO_PERIOD_MAINTAINABILITY_CHANGE_... belongs to a different
        treemap class; it's neither the bare key nor one of its ..._GROUPED_BY_X
        variants, so exact matching never confuses the two."""
        from report_generator.generator.placeholders.implementations.images.treemaps.maintainability_treemap import (
            MaintainabilityPortfolioTreemapPlaceholder as Placeholder,
        )

        report = _fake_report("PORTFOLIO_PERIOD_MAINTAINABILITY_CHANGE_GROUPED_BY_TEAM")

        with (
            patch.object(
                Placeholder, "_determine_resolve_method", return_value="resolve_pptx"
            ),
            patch.object(Placeholder, "value", return_value=None) as mock_value,
        ):
            Placeholder.resolve(report)

        mock_value.assert_not_called()

    def test_resolve_with_two_parameter_lists(self):
        from report_generator.generator.placeholders.implementations.images.treemaps.maintainability_treemap import (
            MaintainabilityMetricPortfolioTreemapPlaceholder as Placeholder,
        )
        from report_generator.generator.utils.constants import MaintMetric

        report = _fake_report(
            *(f"PORTFOLIO_PERIOD_MAINT_{metric}" for metric in MaintMetric)
        )

        with (
            patch.object(
                Placeholder, "_determine_resolve_method", return_value="resolve_pptx"
            ),
            patch.object(Placeholder, "value", return_value=None) as mock_value,
        ):
            Placeholder.resolve(report)

        resolved_metrics = {c.args[0] for c in mock_value.call_args_list}
        assert resolved_metrics == set(MaintMetric)
        for c in mock_value.call_args_list:
            assert c.args[1] == ""
