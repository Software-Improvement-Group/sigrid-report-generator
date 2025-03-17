from datetime import datetime
from functools import cached_property

from report_generator import sigrid_api


class ArchitectureData:
    @cached_property
    def data(self):
        return sigrid_api.get_architecture_findings()

    @cached_property
    def date(self):
        return datetime.strptime(self.data["analysisDate"], '%Y-%m-%d')

    @cached_property
    def ratings(self):
        return self.data['ratings']

    @cached_property
    def system_properties(self):
        return self.ratings['systemProperties']

    @cached_property
    def subcharacteristics(self):
        return self.ratings['subcharacteristics']

    def get_score_for_prop_or_subchar(self, metric_or_subchar):
        return self.system_properties[metric_or_subchar] if metric_or_subchar in self.system_properties else \
            self.subcharacteristics[metric_or_subchar]


architecture_data = ArchitectureData()
