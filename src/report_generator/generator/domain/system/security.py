from functools import cached_property

from report_generator.generator.context import sigrid_api


class SecurityData:
    @cached_property
    def findings(self) -> list:
        return sigrid_api.get_security_findings()

    def count_findings(self, severity) -> int:
        return sum(1 for finding in self.findings if finding["severity"] == severity)

    @cached_property
    def security_rating(self) -> float:
        ratings = sigrid_api.get_security_ratings()
        return ratings.get("rating")


security_data = SecurityData()
