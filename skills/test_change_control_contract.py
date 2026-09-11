from pathlib import Path
import unittest
S=Path(__file__).parent
class T(unittest.TestCase):
 def r(self,n): return (S/n/'SKILL.md').read_text()
 def test_work(self):
  t=self.r('work-issue'); self.assertIn('delegated mode',t); self.assertIn('Do not invoke `fix-all` or `wiggum`',t)
 def test_estimates_are_not_approval_gates(self):
  for name in ('change-control', 'work-issue'):
   with self.subTest(skill=name):
    t=self.r(name)
    self.assertIn('not approval gates',t)
    self.assertIn('Do not invent',t)
    self.assertIn('explicit user limits',t.lower())
    self.assertIn('handoff',t.lower())
 def test_no_automatic_size_or_repair_stops(self):
  removed=(
   'Budget exhaustion means stop and escalate',
   'Stop for undeclared files',
   'or declared file set',
   'undeclared files, or materially larger diff',
   'at most two total repair rounds',
   'at most three attempts',
   'Stop after three unchanged failures',
   'two-round repair budget',
   'same repair budget',
   'Stop on three unchanged failures or exhausted total budget',
  )
  for name in ('change-control', 'work-issue'):
   for phrase in removed:
    with self.subTest(skill=name,phrase=phrase):
     self.assertNotIn(phrase,self.r(name))
 def test_real_scope_and_safety_constraints_remain(self):
  t=self.r('change-control')
  self.assertIn('repository safety rules',t)
  self.assertIn('Discovery is not authorization',t)
  self.assertIn('Unrelated',t)
  self.assertIn('Uncertain',t)
  t=self.r('work-issue')
  self.assertIn('It does not authorize merge',t)
  self.assertIn('deleted work',t)
  self.assertIn('Stop on remote movement or conflicting checkout ownership',t)
  self.assertIn('Never merge',t)
 def test_flow_does_not_restore_removed_budget_gates(self):
  t=(S.parent/'docs'/'change-control-flow.md').read_text()
  self.assertIn('not approval gates',t)
  for phrase in ('within budget?', 'repair round left?', 'same repair budget'):
   self.assertNotIn(phrase,t)
 def test_leaf(self): self.assertIn('do not dispatch a reviewer',self.r('pr-description'))
 def test_diff(self): self.assertIn('return regressions to the root orchestrator',self.r('differential-golden-harness').lower())
 def test_distill(self): self.assertIn('stop after three passes',self.r('distill'))
 def test_campaign(self): self.assertIn('do not run it beneath `work-issue`',self.r('refactor-campaign').lower())
if __name__=='__main__': unittest.main()
