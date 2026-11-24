import unittest
from unittest.mock import patch
import evolution_quality_supervisor_v59 as s
class ProtocolScheduleTests(unittest.TestCase):
    def test_six_paired_windows_preserve_other_work(self):
        phases=[s.phase(h,m) for h in range(24) for m in range(0,60,5)]
        self.assertEqual(phases.count('protocol_research'),6)
        self.assertEqual(phases.count('fleet'),48)
        self.assertEqual(phases.count('tool_research'),6)
        self.assertEqual(phases.count('teacher'),24)
        self.assertEqual(phases.count('distill'),6)
        self.assertEqual(phases.count('evolve_agents'),12)
        self.assertEqual(phases.count('benchmark'),4)
    def test_explicit_dispatch(self):
        with patch('evolution_research_protocol_v67.run',return_value={'status':'completed'}) as run:
            self.assertEqual(s.run('private',7000,'protocol_research'),{'status':'completed'})
            run.assert_called_once_with('private',7000)
if __name__=='__main__':unittest.main()
