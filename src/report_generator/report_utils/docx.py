import logging
import re


def merge_runs_with_same_formatting(paragraph):
    last_run = None
    for run in paragraph.runs:
        if last_run is None:
            last_run = run
            continue
        if has_same_formatting(run, last_run):
            last_run = combine_runs(last_run, run)
            continue
        last_run = run


def has_same_formatting(run, run_2):
    font, font_2 = run.font, run_2.font
    if font.bold != font_2.bold:
        return False
    if font.italic != font_2.italic:
        return False
    if font.name != font_2.name:
        return False
    if font.size != font_2.size:
        return False
    if font.underline != font_2.underline:
        return False
    return True


def combine_runs(base, suffix):
    base.text = base.text + suffix.text
    r_to_remove = suffix._r
    r_to_remove.getparent().remove(r_to_remove)
    return base


def find_text_in_document(document, search_text):
    paragraphs = []
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            if re.match(rf".*\b{search_text}\b.*", run.text):
                paragraphs.append(paragraph)

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if re.match(rf".*\b{search_text}\b.*", run.text):
                            paragraphs.append(paragraph)

    return paragraphs


def update_many_paragraphs(paragraphs, placeholder_id, replacement_text):
    for paragraph in paragraphs:
        update_paragraph(paragraph, placeholder_id, replacement_text)


def update_paragraph(paragraph, placeholder_id, replacement_text):
    if isinstance(replacement_text, (int, float)):
        replacement_text = str(replacement_text)

    run_with_placeholder = None
    if paragraph.runs:
        for run in paragraph.runs:
            if placeholder_id in run.text:
                run_with_placeholder = run
                break

    if run_with_placeholder:
        run_with_placeholder.text = run_with_placeholder.text.replace(placeholder_id, replacement_text)
        logging.debug(
            f"Replacing: {placeholder_id} with \"{replacement_text}\". New text: {run_with_placeholder.text}")
