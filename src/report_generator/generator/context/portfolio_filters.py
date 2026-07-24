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

from collections.abc import Callable
from functools import wraps
from typing import NamedTuple

import click

from report_generator.generator.context import sigrid_api
from report_generator.generator.utils.constants.metadata import (
    METADATA_APPLICATION_TYPE_MAPPING,
    METADATA_BUSINESS_CRITICALITY_MAPPING,
    METADATA_DEPLOYMENT_MAPPING,
    METADATA_DISTRIBUTION_MAPPING,
    METADATA_LIFECYCLE_MAPPING,
    METADATA_TARGET_INDUSTRY_MAPPING,
    METADATA_TECHNOLOGY_CATEGORY_MAPPING,
)


class FilterSpec(NamedTuple):
    value_mapping: (
        dict | None
    )  # Allowed values mapping (key → display label); None means free-form input
    field_label: (
        str | None
    )  # Human-readable field name used in validation error messages
    metadata_key: str  # Key in the portfolio metadata JSON to match against
    transform: (
        Callable | None
    )  # Normalisation applied to the metadata value before comparison


FILTER_CONFIGURATION: dict[str, FilterSpec] = {
    "team": FilterSpec(None, None, "teamNames", None),
    "division": FilterSpec(None, None, "divisionName", None),
    "lifecycle": FilterSpec(
        METADATA_LIFECYCLE_MAPPING, "Lifecycle", "lifecyclePhase", str.upper
    ),
    "deployment": FilterSpec(
        METADATA_DEPLOYMENT_MAPPING,
        "Deployment",
        "deploymentType",
        lambda x: x.upper().replace("-", "_"),
    ),
    "business_criticality": FilterSpec(
        METADATA_BUSINESS_CRITICALITY_MAPPING,
        "Business criticality",
        "businessCriticality",
        str.upper,
    ),
    "distribution": FilterSpec(
        METADATA_DISTRIBUTION_MAPPING,
        "Distribution",
        "softwareDistributionStrategy",
        lambda x: x.upper().replace("-", "_"),
    ),
    "application_type": FilterSpec(
        METADATA_APPLICATION_TYPE_MAPPING,
        "Application type",
        "applicationType",
        lambda x: x.upper().replace("-", "_"),
    ),
    "target_industry": FilterSpec(
        METADATA_TARGET_INDUSTRY_MAPPING, "Target industry", "targetIndustry", str.upper
    ),
    "technology_category": FilterSpec(
        METADATA_TECHNOLOGY_CATEGORY_MAPPING,
        "Technology category",
        "technologyCategory",
        lambda x: x.upper().replace("-", "_"),
    ),
    "main_technology": FilterSpec(None, None, "mainTechnology", str.lower),
    "supplier": FilterSpec(None, None, "supplierNames", None),
}

_filter_state: dict[str, list[str] | None] = {
    name: None for name in FILTER_CONFIGURATION
}


def validate_values(values: list[str], allowed_values: set[str], field: str) -> None:
    invalid = set(values) - allowed_values
    if invalid:
        raise ValueError(f"Invalid value(s) for {field}: {', '.join(sorted(invalid))}")


def process_values(values, mapping, field):
    processed_values = [x.upper().replace("-", "_") for x in values]
    validate_values(values=processed_values, allowed_values=mapping.keys(), field=field)
    return processed_values


def _process_and_set_filter(filter_name: str, value: list[str] | None) -> None:
    if not value:
        return

    spec = FILTER_CONFIGURATION[filter_name]

    if spec.value_mapping:
        processed_value = process_values(
            values=value, mapping=spec.value_mapping, field=spec.field_label
        )
    else:
        processed_value = list(value)

    _filter_state[filter_name] = processed_value


def set_context(**filters: list[str] | None) -> None:
    unknown = filters.keys() - FILTER_CONFIGURATION.keys()
    if unknown:
        allowed = ", ".join(sorted(FILTER_CONFIGURATION.keys()))
        raise ValueError(
            f"Unknown filter(s): {', '.join(sorted(unknown))}. Allowed: {allowed}"
        )
    for filter_name, value in filters.items():
        _process_and_set_filter(filter_name, value)


def reset_context() -> None:
    _filter_state.update({k: None for k in FILTER_CONFIGURATION})


def get_filter_values(filter_name: str) -> list[str] | None:
    if filter_name not in FILTER_CONFIGURATION:
        allowed = ", ".join(sorted(FILTER_CONFIGURATION.keys()))
        raise ValueError(f"Unknown filter: {filter_name}. Allowed: {allowed}")
    return _filter_state[filter_name]


def _build_help(filter_name: str, mapping: dict | None) -> str:
    flag = f"--{filter_name.replace('_', '-')}"
    example_flag = flag
    base = f"[filter] {filter_name.replace('_', ' ').title()} filter, as displayed in Sigrid (multiple values need separate {flag} flags, ie.: {example_flag} aap {example_flag} noot)"
    if mapping:
        allowed = ", ".join(k.lower().replace("_", "-") for k in mapping)
        return f"{base}. Allowed values: {allowed}"
    return base


def portfolio_arguments_command():
    def decorator(func):
        wrapped = wraps(func)(_make_filter_wrapper(func))
        for filter_name, spec in reversed(FILTER_CONFIGURATION.items()):
            flag = f"--{filter_name.replace('_', '-')}"
            wrapped = click.option(
                flag,
                multiple=True,
                help=_build_help(filter_name, spec.value_mapping),
            )(wrapped)
        return wrapped

    return decorator


def _make_filter_wrapper(func):
    def wrapper(*args, **kwargs):
        reset_context()
        filter_kwargs = {
            k: kwargs.pop(k) for k in list(FILTER_CONFIGURATION) if k in kwargs
        }
        set_context(**filter_kwargs)
        return func(*args, **kwargs)

    return wrapper


def _raise_no_systems_found_error():
    """Raise an error when no systems match the specified filters."""
    filter_desc = [
        f"--{name.replace('_', '-')}: {', '.join(values)}"
        for name, values in _filter_state.items()
        if values
    ]

    error_msg = (
        f"No systems match the specified filters.\n"
        f"Filters applied:\n{chr(10).join(filter_desc)}\n\n"
        f"Please verify:\n"
        f"  1. The filter values match exactly as shown in Sigrid (case-sensitive for some fields)\n"
        f"  2. At least one active system exists with these filter criteria\n"
        f"  3. The systems are not marked as development-only"
    )
    raise click.ClickException(error_msg)


def _include_metadata(system_metadata) -> bool:
    return _include(system_metadata["systemName"], [system_metadata])


def _check_if_filters_correct(portfolio_metadata):
    if not any(_include_metadata(s) for s in portfolio_metadata):
        _raise_no_systems_found_error()


def filter_data_on_portfolio_arguments(data_tag=None, system_tag=None):
    """
    This decorator integrates with the Sigrid API to apply portfolio-aware filtering logic to the data returned by the decorated function.
    It ensures that at least one of `data_tag` or `system_tag` is specified to define the filtering context.

    Parameters
    ----------
    data_tag : str, optional
        Tag indicating where system entries are stored in the Sigrid API JSON response.
        E.g.: In `maintainability_portfolio_data`, system entries are available in `maintainability_portfolio_data['systems']`, hence `data_tag='systems'`.
    system_tag : str, optional
        Tag indicating where the system entry's name can be found.
        E.g.: System entries are available in `maintainability_portfolio_data['systems']`, and their system name can be found in `maintainability_portfolio_data['systems']['system']`. Hence: `system_tag='system'`.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if data_tag is None and system_tag is None:
                raise PlaceholderArgumentError(func.__name__)

            data = func(*args, **kwargs)

            if not _are_filters_set():
                return data

            pmd = sigrid_api.get_portfolio_metadata()

            if data_tag:
                filtered_data = _with_data_tag(
                    data=data,
                    portfolio_metadata=pmd,
                    data_tag=data_tag,
                    system_tag=system_tag,
                )
                if not filtered_data[data_tag]:
                    _check_if_filters_correct(pmd)
            else:
                filtered_data = _without_data_tag(
                    data=data, portfolio_metadata=pmd, system_tag=system_tag
                )
                if not filtered_data:
                    _check_if_filters_correct(pmd)

            return filtered_data

        return wrapper

    return decorator


def _with_data_tag(data, portfolio_metadata, data_tag, system_tag):
    systems = [
        entry
        for entry in data[data_tag]
        if _include(
            system_name=entry[system_tag], portfolio_metadata=portfolio_metadata
        )
    ]
    data[data_tag] = systems
    return data


def _without_data_tag(data, portfolio_metadata, system_tag):
    systems = [
        entry
        for entry in data
        if _include(
            system_name=entry[system_tag], portfolio_metadata=portfolio_metadata
        )
    ]
    return systems


def _check_filter_match(
    filter_value: list[str] | None, actual_value, transform
) -> bool:
    """Check if actual value matches filter criteria."""
    if not filter_value:
        return True

    clean_filters = {transform(x) if transform else x for x in filter_value}

    if isinstance(actual_value, list):
        return bool(set(actual_value) & clean_filters)
    return actual_value in clean_filters


def _include(system_name, portfolio_metadata):
    md = _find_system_metadata(
        system_name=system_name, portfolio_metadata=portfolio_metadata
    )
    if md is None:
        return False

    for filter_name, spec in FILTER_CONFIGURATION.items():
        filter_value = _filter_state[filter_name]
        actual_value = md.get(spec.metadata_key)
        if not _check_filter_match(filter_value, actual_value, spec.transform):
            return False

    return True


def _are_filters_set() -> bool:
    return any(v is not None for v in _filter_state.values())


def _find_system_metadata(system_name, portfolio_metadata):
    for s in portfolio_metadata:
        if s["systemName"] == system_name:
            return s
    return None


class PlaceholderArgumentError(Exception):
    def __init__(self, function_name, message="Placeholder argument exception"):
        self.function_name = function_name
        self.message = f"{message} in function '{function_name}'"
        super().__init__(self.message)
