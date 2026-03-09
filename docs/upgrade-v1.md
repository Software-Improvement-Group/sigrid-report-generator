# Upgrading to v1

Version 1 restructures the internal `generator/` package into cleaner sub-namespaces. This is a breaking change
for external Python users who import from the library directly (custom placeholder authors and programmatic
`ReportGenerator` users). **CLI-only users (`report-generator ...`) are unaffected.**

---

## Upgrade scenarios

### Using `ReportGenerator` directly

```python
# before
from report_generator.generator import ReportGenerator

# after
from report_generator import ReportGenerator
```

### Writing a custom `Placeholder`

```python
# before
from report_generator.generator.placeholders import Placeholder
from report_generator.generator.placeholders.base import PlaceholderDocType, ParameterList

# after
from report_generator.generator.placeholders.implementations import Placeholder
from report_generator.generator.placeholders.implementations.base import PlaceholderDocType, ParameterList
```

---

## Full import path reference

### ReportGenerator

| Before | After |
|--------|-------|
| `report_generator.generator.ReportGenerator` | `report_generator.ReportGenerator` |

### sigrid_api

| Before | After |
|--------|-------|
| `report_generator.generator.sigrid_api` | `report_generator.generator.context.sigrid_api` |

### Placeholders (base classes)

| Before | After |
|--------|-------|
| `report_generator.generator.placeholders.Placeholder` | `report_generator.generator.placeholders.implementations.Placeholder` |
| `report_generator.generator.placeholders.base.PlaceholderDocType` | `report_generator.generator.placeholders.implementations.base.PlaceholderDocType` |
| `report_generator.generator.placeholders.base.ParameterList` | `report_generator.generator.placeholders.implementations.base.ParameterList` |

### data_models → domain (all modules, 1:1 rename)

| Before | After |
|--------|-------|
| `report_generator.generator.data_models.*` | `report_generator.generator.domain.*` |
| `report_generator.generator.data_models.portfolio.portfolio_arguments` | `report_generator.generator.context.portfolio_filters` |
| `report_generator.generator.data_models.portfolio.portfolio_utils` | `report_generator.generator.domain.portfolio.shared.utils` |

### constants

| Before | After |
|--------|-------|
| `report_generator.generator.constants` | `report_generator.generator.utils.constants` |

### report_utils

| Before | After |
|--------|-------|
| `report_generator.generator.report_utils.time_series` | `report_generator.generator.utils.time_series` |
| `report_generator.generator.report_utils.pptx` | `report_generator.generator.placeholders.rendering.pptx` |
| `report_generator.generator.report_utils.docx` | `report_generator.generator.placeholders.rendering.docx` |

### formatters

| Before | After |
|--------|-------|
| `report_generator.generator.formatters.formatters` (`calculate_star_rating_integer`, etc.) | `report_generator.generator.utils.star_rating` |
| Other formatters | `report_generator.generator.placeholders.formatting.*` |
