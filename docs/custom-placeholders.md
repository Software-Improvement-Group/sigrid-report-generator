# Custom placeholder examples

> For instructions specific to developers, see [developers.md](developers.md)

## Simple text placeholder

```python
from datetime import datetime

import report_generator

# Custom template
generator = report_generator.ReportGenerator(template_path="location_of_template.pptx")


# Custom placeholder
@report_generator.placeholders.text_placeholder()
def week_number():
    return datetime.now().isocalendar()[1]
```

## Parameterized text placeholder

```python
from report_generator.generator.placeholders import parameterized_text_placeholder


# Custom parameterized placeholder (e.g. LIST_VALUE_1, LIST_VALUE_2, ..., LIST_VALUE_5)
@parameterized_text_placeholder(custom_key="LIST_VALUE_{parameter}",
                                parameters=range(1, 6))
def list_value_for_idx(idx: int):
    return some_value(idx)
```

## Multi-parameter text placeholder

```python
from report_generator.generator.placeholders import parameterized_text_placeholder, MultiParameterList


metrics = ["VOLUME", "DUPLICATION", "UNIT_SIZE", "UNIT_COMPLEXITY"]
groups = ["CHANGED_CODE", "NEW_CODE"]

# Generates keys like MAINT_VOLUME_CHANGED_CODE, MAINT_DUPLICATION_NEW_CODE, etc.
@parameterized_text_placeholder(custom_key="MAINT_{metric}_{group}",
                                parameters=MultiParameterList(metrics, groups))
def maint_metric_by_group(metric: str, group: str):
    return some_value(metric, group)
```

## Multi-parameter class-based placeholder

For full control, extend `ParameterizedPlaceholder` directly. This is useful when you need
custom rendering logic (e.g. for charts or tables) combined with multiple parameters.

```python
from report_generator.generator.placeholders import MultiParameterList, rendering
from report_generator.generator.placeholders.implementations.base import ParameterizedPlaceholder


metrics = ["VOLUME", "DUPLICATION", "UNIT_SIZE", "UNIT_COMPLEXITY"]
groups = ["CHANGED_CODE", "NEW_CODE"]


class MaintMetricByGroup(ParameterizedPlaceholder):
    key = "MAINT_{metric}_{group}"
    allowed_parameters = MultiParameterList(metrics, groups)

    @classmethod
    def value(cls, metric: str, group: str):
        return some_value(metric, group)

    @staticmethod
    def resolve_pptx(presentation, key: str, value_cb) -> None:
        paragraphs = rendering.pptx.find_text_in_presentation(presentation, key)
        if not paragraphs:
            return
        rendering.pptx.update_many_paragraphs(paragraphs, key, value_cb())
```

## Completely custom placeholder

```python
from pptx.chart.data import CategoryChartData

from report_generator.generator.placeholders import Placeholder, rendering


class ComplexChartPlaceholder(Placeholder):
    key = "COMPLEX_CHART"

    @classmethod
    def value(cls, parameter=None):
        return {"labels": ["A", "B", "C"], "axisLabel": "X", "series": [1, 2, 3]}

    @staticmethod
    def resolve_pptx(presentation, key: str, value_cb) -> None:
        charts = [
            shape.chart
            for slide in rendering.pptx.identify_specific_slide(presentation, key)
            for shape in slide.shapes
            if shape.has_chart
        ]

        if len(charts) == 0:
            return

        values = value_cb()
        chart_data = CategoryChartData()
        chart_data.categories = values["labels"]
        [chart_data.add_series(values["axisLabel"], y) for y in values["series"]]
```

## Registering custom placeholders and generating the report

```python
generator.register_additional_placeholders({
    week_number,
    list_value_for_idx,
    maint_metric_by_group,
    MaintMetricByGroup,
    ComplexChartPlaceholder
})

generator.generate("out.pptx")
```
