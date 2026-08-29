from pathlib import Path
import unittest
S=Path(__file__).parent
class T(unittest.TestCase):
 def r(self,n): return (S/n/'SKILL.md').read_text()
 def test_work(self):
  t=self.r('work-issue'); self.assertIn('at most two total repair rounds',t); self.assertIn('delegated mode',t); self.assertIn('Do not invoke `fix-all` or `wiggum`',t)
 def test_leaf(self): self.assertIn('do not dispatch a reviewer',self.r('pr-description'))
 def test_diff(self): self.assertIn('return regressions to the root orchestrator',self.r('differential-golden-harness').lower())
 def test_distill(self): self.assertIn('stop after three passes',self.r('distill'))
 def test_campaign(self): self.assertIn('do not run it beneath `work-issue`',self.r('refactor-campaign').lower())
if __name__=='__main__': unittest.main()
