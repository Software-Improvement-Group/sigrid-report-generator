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
import os
from datetime import date

import click
import requests

from report_generator import ReportGenerator, presets
from report_generator.generator import generator_arguments
from report_generator.generator.context import sigrid_api
from report_generator.generator.placeholders import context as placeholders_context
from report_generator.generator.utils.time_series import add_months
from report_generator.update_check import check_for_update

DEFAULT_START_DATE = add_months(date.today(), -1).strftime("%Y-%m-%d")
DEFAULT_END_DATE = date.today().strftime("%Y-%m-%d")
MATOMO_URL = os.environ.get("MATOMO_URL", "https://sigrid-says.com/usage")


def _normalize_name(ctx, param, value):
    return value.lower() if value else value


_resolve_preset_id = presets.resolve_preset_id


def _resolve_layout(ctx, param, value):
    new_name = _resolve_preset_id(value)
    if new_name != value:
        click.secho(
            f"Warning: layout '{value}' is deprecated and will be discontinued in "
            f"the near future. Use the new name '{new_name}' instead.",
            fg="yellow",
        )
    return new_name


def _validate_system_requirement(system: str | None, layout: str | None) -> None:
    system_required = layout in presets.SYSTEM_LEVEL_PRESETS
    system_provided = system is not None

    if system_required and not system_provided:
        system_presets = ", ".join(sorted(presets.SYSTEM_LEVEL_PRESETS))
        raise click.UsageError(
            f"System is required when using layout '{layout}' "
            f"(required for: {system_presets})"
        )
    elif layout is not None and not system_required and system_provided:
        raise click.UsageError(
            f"System is not allowed when using layout '{layout}' "
            f"(only required for: {', '.join(presets.SYSTEM_LEVEL_PRESETS)})"
        )


def _validate_layout_or_template(ctx, param, value):
    if param.name == "template":
        layout = ctx.params.get("layout")
        template = value

        if template and layout:
            raise click.BadParameter(
                "Both a layout and template are defined. Choose either a predefined layout using -l/--layout, or provide your own report template using -p/--template. Not both"
            )

    return value


@click.command()
@click.version_option(package_name="report-generator", prog_name="report-generator")
@click.option(
    "-d", "--debug", is_flag=True, default=False, help="Enable debug messages"
)
@click.option(
    "-c", "--customer", required=True, callback=_normalize_name, help="Customer name"
)
@click.option(
    "-s",
    "--system",
    required=False,
    callback=_normalize_name,
    help="System name (required for: " + ", ".join(presets.SYSTEM_LEVEL_PRESETS) + ")",
)
@click.option(
    "-t",
    "--token",
    default=lambda: os.environ.get("SIGRID_CI_TOKEN"),
    help="Sigrid CI token for this customer",
)
@click.option(
    "-l",
    "--layout",
    type=click.Choice(presets.ids),
    default="system-snapshot",
    callback=_resolve_layout,
    help="The type of report (mutually exclusive with the -p/--template option)",
)
@click.option(
    "-p",
    "--template",
    type=click.File("rb"),
    callback=_validate_layout_or_template,
    help="A custom report template file (mutually exclusive with the -l/--layout option)",
)
@click.option(
    "--start",
    default=DEFAULT_START_DATE,
    help="Report start date in yyyy-mm-dd, default is last month.",
)
@click.option(
    "--end",
    default=DEFAULT_END_DATE,
    help="Report end date in yyyy-mm-dd, default is last month.",
)
@click.option(
    "-o",
    "--out-file",
    default="out",
    help="write output to this file (default out.pptx/docx)",
)
@click.option(
    "-a",
    "--api-url",
    default=None,
    help=f"Sigrid API base URL, will default to {sigrid_api.DEFAULT_BASE_URL} if not provided",
)
@click.option(
    "-g",
    "--group-by",
    type=click.Choice(placeholders_context.GROUPING_OPTIONS),
    default=placeholders_context.DEFAULT_GROUP_BY,
    help="Metadata dimension all portfolio treemaps are grouped by",
)
@generator_arguments
@click.pass_context
def run(
    _,
    debug,
    customer,
    system,
    token,
    layout,
    template,
    start,
    end,
    out_file,
    api_url,
    group_by,
):
    _configure_logging(debug)
    if not template:
        _validate_system_requirement(system, layout)
    try:
        _configure_api(customer, system, token, (start, end), api_url)
    except ValueError as e:
        raise click.ClickException(str(e)) from e
    placeholders_context.set_group_by(group_by)
    _record_usage_statistics(layout, customer)

    try:
        if template:
            ReportGenerator(template.name).generate(out_file)
        else:
            presets.run(layout, out_file)
    except (
        sigrid_api.SigridAccessDeniedError,
        sigrid_api.SigridTokenInvalidError,
    ) as e:
        raise click.ClickException(str(e)) from e

    _notify_if_update_available()


def _configure_api(
    customer: str,
    system: str,
    token: str,
    period: tuple[str, str],
    api_url: str | None,
):
    sigrid_api.set_context(
        bearer_token=token,
        customer=customer,
        system=system,
        period=period,
        base_url=api_url,
    )


def _record_usage_statistics(layout, customer):
    if os.environ.get("SIGRID_REPORT_GENERATOR_RECORD_USAGE", "1") == "0":
        logging.info("Not recording usage statistics")
        return

    try:
        report_type = layout.replace("-", "") if layout else ""
        requests.get(
            f"{MATOMO_URL}/matomo.php?idsite=5&rec=1&ca=1&e_c=reportgenerator&e_a={report_type}&e_n={customer}"
        )
    except requests.exceptions.ConnectionError:
        logging.warning(
            f"Failed to connect to {MATOMO_URL} for registering usage statistics (not harmful)."
        )


def _notify_if_update_available():
    try:
        message = check_for_update()
        if message:
            click.echo(f"\n{message}")
    except Exception:
        logging.debug("Update check failed", exc_info=True)


def _configure_logging(debug):
    logger = logging.getLogger("root")

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        logging.getLogger("kaleido").setLevel(logging.WARNING)
        logging.getLogger("choreographer").setLevel(logging.WARNING)
        logging.getLogger("matplotlib").setLevel(logging.WARNING)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    formatter.datefmt = "%Y-%m-%d %H:%M:%S"
    ch.setFormatter(formatter)
    logger.addHandler(ch)


if __name__ == "__main__":
    run()
