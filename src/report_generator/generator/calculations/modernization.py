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

class ModernizationScenario:
    def __init__(self, maintainability_data):
        self.maintainability_data = maintainability_data
        
    def calculate_technical_debt(self, optimal_rating = 5.0):
        current_rating = self.maintainability_data.maintainability_rating
        quality_adjustment_factor = 2.0 ** ((current_rating - 3.0) / 2.0)
        build_effort = self.maintainability_data.system_py / quality_adjustment_factor
        renovation_factor = self.calculate_renovation_factor(current_rating, optimal_rating)
        return build_effort * renovation_factor
        
    def calculate_renovation_factor(self, current_rating, target_rating):
        renovation_factors = [
            # 0.5   1.0    2.0    3.0    4.0    5.0    5.5
            [0.000, 0.320, 0.959, 1.638, 1.968, 2.431, 2.662], # 0.5
            [0.000, 0.000, 0.639, 1.318, 1.648, 2.111, 2.343], # 1.0
            [0.000, 0.000, 0.000, 0.679, 1.009, 1.472, 1.704], # 2.0
            [0.000, 0.000, 0.000, 0.000, 0.330, 0.793, 1.025], # 3.0
            [0.000, 0.000, 0.000, 0.000, 0.000, 0.463, 0.695], # 4.0
            [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.232], # 5.0
            [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]  # 5.5
        ]
    
        if current_rating >= target_rating:
            return 0.0
            
        current_index = 0 if current_rating < 1.0 else int(current_rating) 
        target_index = 0 if target_rating < 1.0 else int(target_rating) 
        lower = renovation_factors[current_index][target_index]
        upper = renovation_factors[current_index + 1][target_index]
        return lower + (current_rating - current_index) * (upper - lower)
        