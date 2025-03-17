import logging
from abc import ABC
from typing import Callable, Type

from docx import Document
from pptx.presentation import Presentation

from report_generator import report_utils
from report_generator.placeholders.base import Placeholder, function_name_to_placeholder_key, ParameterizedPlaceholder, \
    Parameter, ParameterList


class _AbstractTextPlaceholder(Placeholder, ABC):
    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable[[], str]) -> None:
        paragraphs = report_utils.pptx.find_text_in_presentation(presentation, key)

        logging.debug(f"Finds for {key}: {len(paragraphs)}")
        if len(paragraphs) == 0:
            return

        value = value_cb()
        report_utils.pptx.update_many_paragraphs(paragraphs, key, value)

    @staticmethod
    def resolve_docx(document: Document, key: str, value_cb: Callable[[], str]):
        paragraphs = report_utils.docx.find_text_in_document(document, key)

        logging.debug(f"Finds for {key}: {len(paragraphs)}")
        if len(paragraphs) == 0:
            return

        value = value_cb()
        report_utils.docx.update_many_paragraphs(paragraphs, key, value)


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
