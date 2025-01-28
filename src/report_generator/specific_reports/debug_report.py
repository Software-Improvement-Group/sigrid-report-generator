from ..powerpoint_report import PowerpointReport
from importlib_resources import files

class DebugReport(PowerpointReport):

    def __init__(self, customer, system, token, out_file):
        super().__init__(customer, system, token, out_file, files("report_generator.templates").joinpath("debug-template.pptx"))
