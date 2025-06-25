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
from abc import ABC
from typing import Callable, Type

from docx import Document
from pptx.presentation import Presentation

from report_generator.generator import report_utils
from report_generator.generator.placeholders.base import Parameter, ParameterList, ParameterizedPlaceholder, \
    Placeholder, \
    PlaceholderDocType, PlaceholderDocsMetadata, function_name_to_placeholder_key


class _DocumentAdapter:
    def __init__(self, find_func, update_func):
        self.find_text = find_func
        self.update_paragraphs = update_func


class _AbstractTextPlaceholder(Placeholder, ABC):
    __doc_metadata__ = PlaceholderDocsMetadata(type=PlaceholderDocType.TEXT)

    _PPTX_ADAPTER = _DocumentAdapter(
        report_utils.pptx.find_text_in_presentation,
        report_utils.pptx.update_many_paragraphs
    )

    _DOCX_ADAPTER = _DocumentAdapter(
        report_utils.docx.find_text_in_document,
        report_utils.docx.update_many_paragraphs
    )

    @staticmethod
    def _resolve_with_adapter(adapter: _DocumentAdapter, document, key: str, value_cb: Callable[[], str]) -> None:
        paragraphs = adapter.find_text(document, key)

        logging.debug(f"Finds for {key}: {len(paragraphs)}")
        if len(paragraphs) == 0:
            return

        value = value_cb()
        if value is None:
            raise ValueError(f"Value for placeholder '{key}' is None")

        adapter.update_paragraphs(paragraphs, key, value)

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable[[], str]) -> None:
        _AbstractTextPlaceholder._resolve_with_adapter(_AbstractTextPlaceholder._PPTX_ADAPTER, presentation, key,
                                                       value_cb)

    @staticmethod
    def resolve_docx(document: Document, key: str, value_cb: Callable[[], str]):
        _AbstractTextPlaceholder._resolve_with_adapter(_AbstractTextPlaceholder._DOCX_ADAPTER, document, key, value_cb)


def text_placeholder(custom_key: str = None) -> Callable[[Callable[[], str]], Type[Placeholder]]:
    def decorator(value_func: Callable[[], str]) -> Type[Placeholder]:
        class TextPlaceholder(_AbstractTextPlaceholder):
            key = custom_key if custom_key else function_name_to_placeholder_key(value_func.__name__)

            @classmethod
            def value(cls, parameter=None) -> str:
                return value_func()


        return TextPlaceholder

    return decorator


def parameterized_text_placeholder(custom_key: str, parameters: ParameterList) -> Callable[
    [Callable[[Parameter], str]], Type[ParameterizedPlaceholder]]:
    def decorator(value_func: Callable[[Parameter], str]) -> Type[ParameterizedPlaceholder]:
        if "{parameter}" not in custom_key:
            raise ValueError("Parameterized text placeholder must have '{parameter}'")


        class ParameterizedTextPlaceholder(ParameterizedPlaceholder, _AbstractTextPlaceholder):
            key = custom_key
            allowed_parameters = parameters

            @classmethod
            def value(cls, parameter: Parameter = None) -> str:
                return value_func(parameter)


        return ParameterizedTextPlaceholder

    return decorator
