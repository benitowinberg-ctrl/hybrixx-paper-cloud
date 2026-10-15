import math
import unittest
from walkforward_research import validate,walk_forward

def candles(n=720):
 return [(1700000000+3600*i,100+0.02*i+2*math.sin(i/19)) for i in range(n)]

class WalkForwardTests(unittest.TestCase):
 def test_quality(self):
  q=validate(candles())
  self.assertEqual(q["missing_intervals"],0)
  self.assertEqual(q["coverage_pct"],100)
 def test_duplicate_rejected(self):
  c=candles();c[2]=(c[1][0],c[2][1])
  with self.assertRaises(ValueError):validate(c)
 def test_gap_rejected(self):
  c=candles();del c[200]
  with self.assertRaises(ValueError):walk_forward(c)
 def test_multiple_folds(self):
  r=walk_forward(candles())
  self.assertEqual(r["fold_count"],3)
  for f in r["folds"]:
   self.assertLessEqual(f["train_end_exclusive"],f["test_start"])
   self.assertEqual(f["cash_benchmark"]["return_pct"],0)
 def test_holdout_not_used_in_training(self):
  a=walk_forward(candles())
  c=candles()
  for i in range(600,len(c)):
   c[i]=(c[i][0],c[i][1]*1.2)
  b=walk_forward(c)
  self.assertEqual(a["folds"][0]["selected_strategy"],b["folds"][0]["selected_strategy"])
if __name__=="__main__":unittest.main()
