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
from report_generator.generator.data_models.portfolio.base import AbstractPortfolioModel

from report_generator.generator.data_models.portfolio.portfolio_arguments import filter_data_on_portfolio_arguments
from report_generator.generator.data_models.system.osh import OSHData, _AnonDataClass

#To import system volume
from report_generator.generator.data_models.portfolio.maintainability_portfolio import maintainability_portfolio_data


class OSHRatingsPortfolioData(AbstractPortfolioModel):
    @cached_property
    @filter_data_on_portfolio_arguments(data_tag="systems", system_tag="systemName")
    def raw_data(self):
        return sigrid_api.get_portfolio_osh_findings()
    
    @cached_property
    def data(self):
        """Returns aggregated library risks for the portfolio."""
        return self.library_risks
    
    @cached_property
    def risks_by_system(self):
        raw_api_data = self.raw_data

        structured_data = {}
        for system in raw_api_data.get("systems", []):
            system_osh_data = OSHData()
            sbom = system['sbom']
            if 'components' not in sbom:
                continue
            system_data = system_osh_data._process_osh_data(sbom)
            system_name = system['systemName']
            structured_data[system_name] = system_data
            # TODO: fix opendemo error
        
        return structured_data

    @cached_property
    def library_risks(self):
        all_risks = _AnonDataClass()

        for system_name in self.risks_by_system:
            system_data = self.risks_by_system[system_name]
            all_risks.total_deps += system_data.total_deps
            
            # For now: Copy date from the first system with data (all should be similar) TODO: update to correct dates
            if all_risks.date_year == "" and system_data.date_year != "":
                all_risks.date_year = system_data.date_year
                all_risks.date_month = system_data.date_month
                all_risks.date_day = system_data.date_day
            
            for i in range(5):
                all_risks.vuln_risks[i] += system_data.vuln_risks[i]
                all_risks.license_risks[i] += system_data.license_risks[i]
                all_risks.freshness_risks[i] += system_data.freshness_risks[i]
                all_risks.stability_risks[i] += system_data.stability_risks[i]
                all_risks.mgmt_risks[i] += system_data.mgmt_risks[i]
                all_risks.activity_risks[i] += system_data.activity_risks[i]
            all_risks.vulns.extend(system_data.vulns)
        
        return all_risks
    
    def _find_first_nonzero_risk(self, category_risks):
        """Find the first non-zero risk level in a category."""
        for risk_level in range(4):  # 0=critical, 1=high, 2=medium, 3=low
            if category_risks[risk_level] > 0:
                return risk_level
        return 4  # no_risk
    
    def _get_highest_risk_level(self, system_data):
        """Determine the highest risk level for a system across all OSH categories."""
        all_categories = [
            system_data.vuln_risks, system_data.license_risks, system_data.freshness_risks,
            system_data.stability_risks, system_data.mgmt_risks, system_data.activity_risks
        ]
        
        highest_risk = 4  # Start with no_risk
        for category_risks in all_categories:
            category_highest = self._find_first_nonzero_risk(category_risks)
            highest_risk = min(highest_risk, category_highest)
        
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
        
        for system_name in self.risks_by_system:
            system_data = self.risks_by_system[system_name]
            highest_risk = self._get_highest_risk_level(system_data)
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
        total_vulns = self.data.total_vulnerable
        if total_vulns > 0:
            pct_vulns = max(total_vulns / self.data.total_deps,
                            0.01)  # Percentage should always be at least 1. 0% looks stupid.
            return f"{pct_vulns:.0%} of dependencies ({total_vulns} in total) used in the system contain one or more known vulnerabilities."
        else:
            return "The system is free of known vulnerabilities."

    @property
    def freshness_summary(self):
        total_outdated = sum(self.data.freshness_risks[
                                 0:3])  # Only count critial+high+medium risk. Llow is fresh enough to not report on
        if total_outdated > 0:
            pct_outdated = max(total_outdated / self.data.total_deps, 0.01)
            return f"{pct_outdated:.0%} of dependencies ({total_outdated} in total) used in the system have not been updated for over 2 years."
        else:
            return "All dependencies in the system have been updated in the last 2 years."

    @property
    def legal_summary(self):
        total_legal = sum(self.data.license_risks[
                              0:3])  # Only count critial, high, and medium. Low license risk is typically not restrictive, so not interesting to report on
        if total_legal > 0:
            pct_legal = max(total_legal / self.data.total_deps, 0.01)
            return f"{pct_legal:.0%} of dependencies ({total_legal} in total) uses a potentially restrictive open-source license (e.g. GPL/AGPL)."
        else:
            return "All dependencies in the system use relatively liberal open-source licenses."

    @property
    def management_summary(self):
        total_unmanaged = sum(self.data.mgmt_risks[0:4])
        if total_unmanaged > 0:
            pct_unmanaged = max(total_unmanaged / self.data.total_deps, 0.01)
            return f"{pct_unmanaged:.0%} of dependencies ({total_unmanaged} in total) does not use a package manager but is placed in the codebase directly."
        else:
            return "All dependencies in the system are managed by a package manager."
    
    @cached_property
    def period(self):
        return None, sigrid_api.get_period()[1]
    
    def get_system(self, system):
        return AbstractPortfolioModel._get_system_helper(system, self.raw_data['systems'], 'systemName')
    
    def find_system(self, system):
        return self.get_system(system)

    @cached_property
    def system_names(self):
        return AbstractPortfolioModel._system_names_helper(self.raw_data['systems'], 'systemName')
    
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
        counts = {"above_market": 0, "market_average": 0, "below_market": 0}
        total_systems = 0
        
        for system in self.raw_data.get('systems', []):
            rating = self._extract_osh_rating(system, 'system')
            if rating is None:
                continue
            
            total_systems += 1
            category = self._categorize_rating(rating)
            counts[category] += 1
        
        return self._calculate_percentages(counts, total_systems)
    
    def _get_volume_from_maintainability(self, system_name):
        """Get volume from maintainability portfolio for a given system."""
        try:
            end_snapshot = maintainability_portfolio_data.end_snapshot(system_name)
            return end_snapshot.get('volumeInPersonMonths', 0) if end_snapshot else 0
        except:
            return 0
    
    def _get_rating_and_volume(self, system):
        """Extract rating and volume for a system."""
        rating = self._extract_osh_rating(system, 'system')
        system_name = system.get('systemName')
        
        if rating is None or system_name is None:
            return None, 0
        
        volume = self._get_volume_from_maintainability(system_name)
        return rating, volume
    
    @cached_property
    def weighted_average_rating(self):
        """Calculate volume-weighted average OSH rating across all systems."""
        total_weighted_rating = 0
        total_volume = 0
        
        for system in self.raw_data.get('systems', []):
            rating, volume = self._get_rating_and_volume(system)
            
            if rating is None or volume == 0:
                continue
            
            total_weighted_rating += rating * volume
            total_volume += volume
        
        if total_volume > 0:
            return self._round_star_rating(total_weighted_rating / total_volume)
        return 0.0

osh_portfolio_data = OSHRatingsPortfolioData()