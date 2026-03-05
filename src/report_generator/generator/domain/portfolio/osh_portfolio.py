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

from functools import cached_property

from report_generator.generator import sigrid_api
from report_generator.generator.context.portfolio_filters import filter_data_on_portfolio_arguments
from report_generator.generator.domain.shared.osh_base import OSHMetricsBase
from report_generator.generator.domain.portfolio.base import AbstractPortfolioModel
from report_generator.generator.domain.portfolio.shared import utils


class OSHRatingsPortfolioData(OSHMetricsBase, AbstractPortfolioModel):
    @cached_property
    @filter_data_on_portfolio_arguments(data_tag="systems", system_tag="systemName")
    def raw_data(self):
        return sigrid_api.get_portfolio_osh_findings()
    
    @cached_property
    def dependencies_count(self) -> int:
        """Total number of dependencies across all systems."""
        total = 0
        for system in self.raw_data.get("systems", []):
            sbom = system.get('sbom', {})
            total += len(sbom.get('components', []))
        return total
    
    def _get_risk_distribution_for_metric(self, metric_property: str) -> list[int]:
        """Returns aggregated risk distribution as [critical, high, medium, low, no_risk] counts."""
        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, None: 0}
        
        for system in self.raw_data.get("systems", []):
            sbom = system.get('sbom', {})
            for component in sbom.get("components", []):
                properties = component.get("properties", [])
                risk = self._find_property_value(properties, metric_property)
                risk_counts[risk if risk in risk_counts else None] += 1
        
        return [risk_counts["CRITICAL"], risk_counts["HIGH"], risk_counts["MEDIUM"], 
                risk_counts["LOW"], risk_counts[None]]
    
    def _find_property_value(self, properties, key):
        """Find a property value by key in a list of properties."""
        for prop in properties:
            if prop.get("name") == key:
                return prop.get("value")
        return None
    
    @cached_property
    def vulnerability_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric("sigrid:risk:vulnerability")
    
    @cached_property
    def legal_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric("sigrid:risk:legal")
    
    @cached_property
    def freshness_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric("sigrid:risk:freshness")
    
    @cached_property
    def stability_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric("sigrid:risk:stability")
    
    @cached_property
    def management_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric("sigrid:risk:management")
    
    @cached_property
    def activity_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric("sigrid:risk:activity")
    
    @cached_property
    def date(self):
        """Returns the end date of the analysis period as a datetime object."""
        from datetime import datetime
        _, end_date = self.period
        return datetime.strptime(end_date, "%Y-%m-%d")
    
    def _find_first_nonzero_risk(self, category_risks):
        """Find the first non-zero risk level in a category."""
        for risk_level in range(4):  # 0=critical, 1=high, 2=medium, 3=low
            if category_risks[risk_level] > 0:
                return risk_level
        return 4  # no_risk
    
    def _get_highest_risk_level_for_system(self, system_name):
        """Determine the highest risk level for a system across all OSH categories."""
        highest_risk = 4  # Start with no_risk
        
        for system in self.raw_data.get("systems", []):
            if system.get('systemName') != system_name:
                continue
            
            sbom = system.get('sbom', {})
            for component in sbom.get('components', []):
                properties = component.get('properties', [])
                
                # Check all risk categories for this component
                for metric in ['sigrid:risk:vulnerability', 'sigrid:risk:legal', 'sigrid:risk:freshness',
                             'sigrid:risk:stability', 'sigrid:risk:management', 'sigrid:risk:activity']:
                    risk = self._find_property_value(properties, metric)
                    risk_mapping = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
                    risk_level = risk_mapping.get(risk, 4)
                    highest_risk = min(highest_risk, risk_level)
        
        return highest_risk
    
    def _categorize_risk_level(self, risk_level, risk_counts):
        """Increment the appropriate risk count based on the risk level."""
        risk_mapping = {0: 'critical', 1: 'high', 2: 'medium', 3: 'low', 4: 'no_risk'}
        category = risk_mapping.get(risk_level, 'no_risk')
        risk_counts[category] += 1
    
    @cached_property
    def system_risk_levels(self):
        """Calculate the highest risk level for each system and count systems by risk level."""
        risk_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'no_risk': 0}
        
        for system in self.raw_data.get("systems", []):
            system_name = system.get('systemName')
            if not system_name:
                continue
            
            highest_risk = self._get_highest_risk_level_for_system(system_name)
            self._categorize_risk_level(highest_risk, risk_counts)
        
        return risk_counts
    
    def _get_library_identifier(self, component):
        """Create unique identifier for a library."""
        return f"{component.get('name', '')}:{component.get('version', '')}"
    
    def _get_library_risk_levels(self, component):
        """Get risk levels across all categories for a library component."""
        props = component.get('properties', [])
        return [
            self._get_risk_value(props, 'sigrid:risk:vulnerability'),
            self._get_risk_value(props, 'sigrid:risk:legal'),
            self._get_risk_value(props, 'sigrid:risk:freshness'),
            self._get_risk_value(props, 'sigrid:risk:stability'),
            self._get_risk_value(props, 'sigrid:risk:management'),
            self._get_risk_value(props, 'sigrid:risk:activity')
        ]
    
    def _process_component(self, component, processed_libraries, risk_counts):
        """Process a single component and update risk tracking."""
        lib_id = self._get_library_identifier(component)
        lib_risks = self._get_library_risk_levels(component)
        highest_risk = min(lib_risks)
        
        if lib_id not in processed_libraries or highest_risk < processed_libraries[lib_id]:
            if lib_id in processed_libraries:
                self._decrement_risk_count(risk_counts, processed_libraries[lib_id])
            processed_libraries[lib_id] = highest_risk
            self._categorize_risk_level(highest_risk, risk_counts)
    
    @cached_property
    def library_risk_levels(self):
        """Calculate risk level counts for libraries, counting each library once by its highest risk."""
        risk_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'no_risk': 0}
        processed_libraries = {}
        
        for system in self.raw_data.get("systems", []):
            sbom = system.get('sbom', {})
            components = sbom.get('components', [])
            
            for component in components:
                self._process_component(component, processed_libraries, risk_counts)
        
        return risk_counts
    
    def _get_risk_value(self, properties, risk_name):
        """Extract risk value from component properties."""
        risk_mapping = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        
        for prop in properties:
            if prop.get('name') == risk_name:
                risk = prop.get('value', 'UNKNOWN')
                return risk_mapping.get(risk, 4)
        return 4  # no_risk
    
    def _decrement_risk_count(self, risk_counts, risk_level):
        """Decrement the count for a risk level."""
        risk_mapping = {0: 'critical', 1: 'high', 2: 'medium', 3: 'low', 4: 'no_risk'}
        category = risk_mapping.get(risk_level, 'no_risk')
        risk_counts[category] -= 1
    
    @property
    def vulnerability_summary(self):
        total_vulns = self.vulnerabilities_count
        if total_vulns > 0:
            pct_vulns = max(total_vulns / self.dependencies_count,
                            0.01)  # Percentage should always be at least 1. 0% looks stupid.
            return f"{pct_vulns:.0%} of dependencies ({total_vulns} in total) used in the system contain one or more known vulnerabilities."
        else:
            return "The system is free of known vulnerabilities."

    @property
    def freshness_summary(self):
        total_outdated = sum(self.freshness_risk_distribution[
                                 0:3])  # Only count critial+high+medium risk. Low is fresh enough to not report on
        if total_outdated > 0:
            pct_outdated = max(total_outdated / self.dependencies_count, 0.01)
            return f"{pct_outdated:.0%} of dependencies ({total_outdated} in total) used in the system have not been updated for over 2 years."
        else:
            return "All dependencies in the system have been updated in the last 2 years."

    @property
    def legal_summary(self):
        total_legal = sum(self.legal_risk_distribution[
                              0:3])  # Only count critial, high, and medium. Low license risk is typically not restrictive, so not interesting to report on
        if total_legal > 0:
            pct_legal = max(total_legal / self.dependencies_count, 0.01)
            return f"{pct_legal:.0%} of dependencies ({total_legal} in total) uses a potentially restrictive open-source license (e.g. GPL/AGPL)."
        else:
            return "All dependencies in the system use relatively liberal open-source licenses."

    @property
    def management_summary(self):
        total_unmanaged = sum(self.management_risk_distribution[0:4])
        if total_unmanaged > 0:
            pct_unmanaged = max(total_unmanaged / self.dependencies_count, 0.01)
            return f"{pct_unmanaged:.0%} of dependencies ({total_unmanaged} in total) does not use a package manager but is placed in the codebase directly."
        else:
            return "All dependencies in the system are managed by a package manager."
    
    @cached_property
    def period(self):
        return None, sigrid_api.get_period()[1]
    
    def get_system(self, system):
        return utils.get_system_helper(system, self.raw_data['systems'], 'systemName')
    
    def find_system(self, system):
        return self.get_system(system)

    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.raw_data['systems'], 'systemName')
    
    def get_score_for_prop(self, prop):
        """Calculate aggregated rating for a specific OSH metric across all systems."""
        ratings = []
        for system in self.raw_data.get('systems', []):
            rating = self._extract_osh_rating(system, prop)
            if rating is not None:
                ratings.append(rating)
        
        # Return average rating across all systems, or 0.0 if no ratings found
        return sum(ratings) / len(ratings) if ratings else 0.0
    
    def _extract_osh_rating(self, system, property_name):
        """Extract a specific OSH rating from a system's SBOM metadata."""
        sbom = system.get('sbom', {})
        metadata = sbom.get('metadata', {})
        properties = metadata.get('properties', [])
        
        for property in properties:
            if property.get('name') == f'sigrid:ratings:{property_name}':
                try:
                    return float(property.get('value', 0))
                except (ValueError, TypeError):
                    pass
        return None
    
    @cached_property
    def get_rating_distribution_percentages(self):
        """Calculate the percentage of systems above market, at market average, and below market average."""
        return utils.get_rating_distribution_percentages(
            self.raw_data.get('systems', []),
            lambda system: self._extract_osh_rating(system, 'system')
        )
    
    def _get_rating_and_volume(self, system):
        """Extract rating and volume for a system."""
        return utils.get_rating_and_volume_from_system(
            system,
            lambda s: self._extract_osh_rating(s, 'system'),
            'systemName'
        )
    
    @cached_property
    def weighted_average_rating(self):
        """Calculate volume-weighted average OSH rating across all systems."""
        return utils.calculate_weighted_average_rating(
            self.raw_data.get('systems', []),
            self._get_rating_and_volume
        )

osh_portfolio_data = OSHRatingsPortfolioData()