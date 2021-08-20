from core.analyzis.waves_analyzis import WaveComparer
from core.simulation_case.case import Case
from core.simulation_case.case import Case
from core.utils.files import get_project_root
import os

os.chdir(f'{get_project_root()}/cases/pacific')

case = Case('./pacific_example.json')
comparer = WaveComparer(case=case,
                        output_files=['./results/P1_pacific_example_20180102.000000_20180103.230000.tab',
                                      './results/P2_pacific_example_20180102.000000_20180103.230000.tab'])
comparer.compare_with_rean()
