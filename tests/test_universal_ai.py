import tempfile
import unittest
from pathlib import Path
from universal_ai.memory import MemoryStore
from universal_ai.planner import Step,evaluate

class UniversalAITests(unittest.TestCase):
 def test_memory_provenance_search_and_delete(self):
  with tempfile.TemporaryDirectory() as directory:
   store=MemoryStore(Path(directory)/"memory.json")
   store.remember("fact1","Test observation","unit-test","2026-10-15T19:00:00+00:00")
   self.assertEqual(len(store.search("observation")),1)
   self.assertEqual(store.search("observation")[0]["source"],"unit-test")
   self.assertTrue(store.forget("fact1"))
   self.assertEqual(store.search("observation"),[])
 def test_duplicate_memory_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   store=MemoryStore(Path(directory)/"memory.json")
   store.remember("x","first","test")
   with self.assertRaises(ValueError):store.remember("x","second","test")
 def test_read_only_and_approval(self):
  r=evaluate([Step("memory.search","x"),Step("memory.forget","x"),Step("memory.forget","x",True)])
  self.assertEqual([x["allowed"] for x in r["steps"]],[True,False,True])
  self.assertEqual(r["executed_tools"],0)
 def test_unknown_tool_is_denied(self):
  self.assertFalse(evaluate([Step("trade.transfer","all",True)])["steps"][0]["allowed"])
if __name__=="__main__":unittest.main()
