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

import functools
import itertools
import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Union

from report_generator.generator.context.sigrid_api import SigridAPIRequestFailedError
from report_generator.generator.report import Report, ReportType

Parameter = Union[str, int, Enum]
ParameterList = Iterable[Parameter]


class MultiParameterList:
    """Multiple parameter lists for cartesian product iteration."""

    def __init__(self, *param_lists: ParameterList):
        self.param_lists: tuple[list[Parameter], ...] = tuple(
            list(pl) for pl in param_lists
        )

    @property
    def arity(self) -> int:
        return len(self.param_lists)

    def product(self) -> Iterable[tuple[Parameter, ...]]:
        return itertools.product(*self.param_lists)


CAMEL_TO_SNAKE_PATTERN = re.compile(
    r"(?<!^)(?=[A-Z][a-z])|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])"
)
PARAMETER_TOKEN_PATTERN = re.compile(r"\{[^}]+\}")


def class_name_to_placeholder_key(class_name: str):
    return CAMEL_TO_SNAKE_PATTERN.sub("_", class_name).upper()


def function_name_to_placeholder_key(function_name: str):
    return function_name.upper()


class PlaceholderDocType(Enum):
    TEXT = "Text"
    CHART = "Chart"
    TABLE = "Table"
    IMAGE = "Image"
    OTHER = "Other"


@dataclass
class Placeholder(ABC):
    """
    Abstract base class representing a dynamic element (placeholder) in a report.

    A Placeholder maps a specific key (string identifier) in a document template
    to a dynamically calculated value. It handles the logic of resolving that value
    into specific document formats (e.g., PowerPoint, Word) based on the ReportType.

    Attributes:
        key (str): The identifier string found in the report template (e.g., 'PROJECT_NAME').
        __doc_type__ (PlaceholderDocType): The type of content this placeholder produces.
                                           Defaults to PlaceholderDocType.OTHER.
    """

    key: str
    __doc_type__: PlaceholderDocType = PlaceholderDocType.OTHER
    __placeholder__ = True

    @classmethod
    @abstractmethod
    def value(cls):
        pass

    @classmethod
    def resolve(cls, report: Report) -> None:
        resolve_method_name = cls._determine_resolve_method(report.type)
        if not resolve_method_name:
            return
        cls._call_resolve_method(resolve_method_name, report, cls.key, cls.value)

    @classmethod
    def _call_resolve_method(cls, resolve_method_name, report, key, value_fn):
        try:
            getattr(cls, resolve_method_name)(report, key, value_fn)
        except SigridAPIRequestFailedError as e:
            logging.info(f"Failed to resolve {key}: {e}")
        except (KeyError, AttributeError, ValueError) as e:
            logging.warning(
                f"Failed to resolve {key}: Value not found ({type(e).__name__}: {e})"
            )

    @classmethod
    def _determine_resolve_method(cls, report_type: ReportType):
        if report_type == ReportType.PRESENTATION and hasattr(cls, "resolve_pptx"):
            return "resolve_pptx"
        elif report_type == ReportType.DOCUMENT and hasattr(cls, "resolve_docx"):
            return "resolve_docx"
        else:
            return None

    @classmethod
    def supports(cls, report_type: ReportType) -> bool:
        return cls._determine_resolve_method(report_type) is not None

    @classmethod
    def is_parameterized(cls):
        return getattr(cls, "__parameterized_placeholder__", False)


class ParameterizedPlaceholder(Placeholder, ABC):
    """
    A specialized Placeholder that expands into multiple values based on a list of parameters.

    Instead of a single key, this class iterates over `allowed_parameters` to generate
    multiple dynamic keys. It expects the `key` attribute to contain a formatting marker
    (specifically `{parameter}`) which is replaced during resolution.

    Attributes:
        allowed_parameters (ParameterList): A list of values (str, int, or Enum) used to
                                            generate unique keys and calculate values.
    """

    __parameterized_placeholder__ = True
    allowed_parameters: ParameterList

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "key" in cls.__dict__ and "allowed_parameters" in cls.__dict__:
            cls._validate_key_token_count()

    @classmethod
    def _expected_arity(cls) -> int:
        if isinstance(cls.allowed_parameters, MultiParameterList):
            return cls.allowed_parameters.arity
        return 1

    @classmethod
    def _validate_key_token_count(cls):
        actual = len(PARAMETER_TOKEN_PATTERN.findall(cls.key))
        expected = cls._expected_arity()
        if actual != expected:
            raise ValueError(
                f"Parameterized placeholder key must have {expected} "
                f"{{...}} token(s), found {actual}: {cls.key}"
            )

    @classmethod
    def resolve(cls, report: Report) -> None:
        resolve_method_name = cls._determine_resolve_method(report.type)
        if not resolve_method_name:
            return
        if isinstance(cls.allowed_parameters, MultiParameterList):
            cls._resolve_multi(resolve_method_name, report)
        else:
            cls._resolve_single(resolve_method_name, report)

    @classmethod
    def _resolve_single(cls, resolve_method_name: str, report: Report) -> None:
        for parameter in cls.allowed_parameters:
            key_with_param = PARAMETER_TOKEN_PATTERN.sub(
                str(parameter), cls.key, count=1
            )
            value_cb = functools.partial(cls.value, parameter)
            cls._call_resolve_method(
                resolve_method_name, report, key_with_param, value_cb
            )

    @classmethod
    def _resolve_multi(cls, resolve_method_name: str, report: Report) -> None:
        for param_tuple in cls.allowed_parameters.product():
            key_with_params = cls.key
            for param in param_tuple:
                key_with_params = PARAMETER_TOKEN_PATTERN.sub(
                    str(param), key_with_params, count=1
                )
            value_cb = functools.partial(cls.value, *param_tuple)
            cls._call_resolve_method(
                resolve_method_name, report, key_with_params, value_cb
            )
