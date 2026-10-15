import unittest
from learning_engine import OnlineLogistic,run_market,run_all
from strategy_research import PAIRS

def candles(n=240):
 return [(1700000000+i*3600,100+0.08*i+0.9*((i%7)-3)) for i in range(n)]

class LearningEngineTests(unittest.TestCase):
 def test_deterministic_holdout(self):
  a=run_market(candles())
  b=run_market(candles())
  self.assertEqual(a,b)
  self.assertTrue(a["holdout_model_frozen"])
  self.assertFalse(a["signal_authorized"])
 def test_future_change_does_not_change_model_weights(self):
  a=candles()
  b=list(a)
  for i in range(200,len(b)):
   b[i]=(b[i][0],b[i][1]*1.1)
  self.assertEqual(run_market(a)["model_weights"],run_market(b)["model_weights"])
 def test_short_history_fails(self):
  with self.assertRaises(ValueError):run_market(candles(100))
 def test_no_order_authorization(self):
  report=run_all({coin:candles() for coin in PAIRS})
  self.assertEqual(len(report["assets"]),10)
  self.assertFalse(report["trade_authorization"])
 def test_invalid_timestamps_fail(self):
  c=candles()
  c[100]=(c[99][0],c[100][1])
  with self.assertRaises(ValueError):run_market(c)
 def test_model_learns_from_labels(self):
  model=OnlineLogistic()
  p=model.predict_one((0,0,0,0,0))
  model.learn_one((0,0,0,0,0),1)
  self.assertGreater(model.predict_one((0,0,0,0,0)),p)

if __name__=="__main__":unittest.main()
