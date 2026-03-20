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


class TestTreemapImagePlaceholder:
    """Test cases for treemap image generation with empty data handling."""

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemap_image.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemap_image.tr"
    )
    def test_draw_image_with_empty_dataframe_returns_none(self, mock_treemap, mock_plt):
        """Test that draw_image returns None when dataframe is empty."""
        from report_generator.generator.placeholders.implementations.images.treemap_image import (
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
        "report_generator.generator.placeholders.implementations.images.treemap_image.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemap_image.tr"
    )
    def test_draw_image_with_empty_color_mapping_creates_default(
        self, mock_treemap, mock_plt
    ):
        """Test that draw_image creates default color mapping when empty."""
        from report_generator.generator.placeholders.implementations.images.treemap_image import (
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

        # Should have called treemap with a non-empty color mapping
        assert mock_treemap.treemap.called
        call_kwargs = mock_treemap.treemap.call_args[1]
        assert "cmap" in call_kwargs
        assert len(call_kwargs["cmap"]) == 2  # Should have colors for both systems
        assert "system1" in call_kwargs["cmap"]
        assert "system2" in call_kwargs["cmap"]

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemap_image.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemap_image.tr"
    )
    def test_draw_image_with_invalid_dimensions_returns_none(
        self, mock_treemap, mock_plt
    ):
        """Test that draw_image returns None with invalid dimensions."""
        from report_generator.generator.placeholders.implementations.images.treemap_image import (
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
        "report_generator.generator.placeholders.implementations.images.treemap_image.plt"
    )
    def test_draw_image_with_none_fig_data_returns_none(self, mock_plt):
        """Test that draw_image returns None when fig_data is None."""
        from report_generator.generator.placeholders.implementations.images.treemap_image import (
            _AbstractPortfolioTreemapPlaceholder,
        )

        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, None)
        assert result is None

    @patch(
        "report_generator.generator.placeholders.implementations.images.treemap_image.plt"
    )
    @patch(
        "report_generator.generator.placeholders.implementations.images.treemap_image.tr"
    )
    def test_draw_image_with_valid_data_creates_treemap(self, mock_treemap, mock_plt):
        """Test that draw_image creates treemap with valid data and color mapping."""
        from report_generator.generator.placeholders.implementations.images.treemap_image import (
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
        # Treemap should be called with the provided color mapping
        mock_treemap.treemap.assert_called_once()
        call_kwargs = mock_treemap.treemap.call_args[1]
        assert call_kwargs["cmap"] == fig_data["color_mapping"]
        # Axes should be turned off
        mock_ax.axis.assert_called_once_with("off")
