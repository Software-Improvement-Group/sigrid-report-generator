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

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Union

from report_generator.generator.report import Report, ReportType
from report_generator.generator.sigrid_api import SigridAPIRequestFailed

Parameter = Union[str, int, Enum]
ParameterList = Iterable[Parameter]

CAMEL_TO_SNAKE_PATTERN = re.compile(r'(?<!^)(?=[A-Z][a-z])|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')


def class_name_to_placeholder_key(class_name: str):
    return CAMEL_TO_SNAKE_PATTERN.sub('_', class_name).upper()


def function_name_to_placeholder_key(function_name: str):
    return function_name.upper()


class PlaceholderDocType(Enum):
    TEXT = 'Text'
    CHART = 'Chart'
    OTHER = 'Other'


@dataclass
class PlaceholderDocsMetadata:
    type: PlaceholderDocType
    subject: str = None
    example_output: str = None

@dataclass
class Placeholder(ABC):
    __placeholder__ = True
    key: str
    __doc_metadata__: PlaceholderDocsMetadata = PlaceholderDocsMetadata(type=PlaceholderDocType.OTHER)

    @classmethod
    @abstractmethod
    def value(cls, parameter: Parameter = None):
        pass

    @classmethod
    def resolve(cls, report: Report) -> None:
        resolve_method_name = cls._determine_resolve_method(report.type)

        if not resolve_method_name:
            return

        try:
            getattr(cls, resolve_method_name)(report, cls.key, cls.value)
        except SigridAPIRequestFailed as e:
            logging.info(f'Failed to resolve {cls.key}: {e}')
        except (KeyError, AttributeError, ValueError) as e:
            logging.warning(f'Failed to resolve {cls.key}: Value not found ({type(e).__name__}: {e})')

    @classmethod
    def _determine_resolve_method(cls, report_type: ReportType):
        if report_type == ReportType.PRESENTATION and hasattr(cls, 'resolve_pptx'):
            return 'resolve_pptx'
        elif report_type == ReportType.DOCUMENT and hasattr(cls, 'resolve_docx'):
            return 'resolve_docx'
        else:
            return None

    @classmethod
    def supports(cls, report_type: ReportType) -> bool:
        return cls._determine_resolve_method(report_type) is not None

    @classmethod
    def is_parameterized(cls):
        return getattr(cls, '__parameterized_placeholder__', False)


class ParameterizedPlaceholder(Placeholder, ABC):
    __parameterized_placeholder__ = True
    allowed_parameters: ParameterList

    @classmethod
    def resolve(cls, report: Report) -> None:
        resolve_method_name = cls._determine_resolve_method(report.type)

        if not resolve_method_name:
            return

        for parameter in cls.allowed_parameters:
            key_p = cls.key.replace('{parameter}', str(parameter))

            try:
                value_p = lambda: cls.value(parameter)
                getattr(cls, resolve_method_name)(report, key_p, value_p)
            except SigridAPIRequestFailed as e:
                logging.info(f'Failed to resolve {key_p}: {e}')
