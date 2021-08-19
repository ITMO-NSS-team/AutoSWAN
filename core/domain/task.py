from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SimulationTask:
    simulation_start: datetime
    simulation_end: datetime
    variables: List[str] = None
    spinup_start: Optional[datetime] = None
    integration_step: str = '10 MIN'
    model: str = 'SWAN_32'

    def __post_init__(self):
        if not self.spinup_start:
            self.spinup_start = self.simulation_start

        if self.spinup_start > self.simulation_start:
            raise ValueError('spinup_start should be before simulation_start')

        if self.simulation_start >= self.simulation_end:
            raise ValueError('simulation_start should be before simulation_end')

        if not self.variables:
            self.variables = ['HSig', 'DIR', 'PDIR']

        if not self.model:
            self.model = 'SWAN_32'
