from core.domain.task import SimulationTask


def month_range(year: int, task: SimulationTask):
    start_month = 1
    end_month = 12
    if year == task.spinup_start.year:
        start_month = task.spinup_start.month
    if year == task.simulation_end.year:
        end_month = task.simulation_end.month
    return start_month, end_month
