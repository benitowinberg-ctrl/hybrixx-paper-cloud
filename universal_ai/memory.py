"""HYBRIXX universal AI MVP: local provenance memory, no model or tool access.

This module is deliberately offline and independent from trading.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

MAX_ITEMS=1000
MAX_TEXT=4000

def validate_record(record):
    if not isinstance(record,dict):
        raise ValueError("INVALID_RECORD")
    for key in ("id","text","source","created_utc"):
        if not isinstance(record.get(key),str) or not record[key].strip():
            raise ValueError("MISSING_"+key.upper())
    if len(record["text"])>MAX_TEXT or len(record["id"])>128 or len(record["source"])>512:
        raise ValueError("FIELD_TOO_LONG")
    stamp=datetime.fromisoformat(record["created_utc"].replace("Z","+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("NAIVE_TIMESTAMP")
    return record

class MemoryStore:
    def __init__(self,path):
        self.path=Path(path)
    def read(self):
        if not self.path.exists():
            return []
        data=json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data,list) or len(data)>MAX_ITEMS:
            raise ValueError("INVALID_MEMORY_STORE")
        records=[validate_record(x) for x in data]
        if len({x["id"] for x in records})!=len(records):
            raise ValueError("DUPLICATE_IDS")
        return records
    def _write(self,records):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        tmp.replace(self.path)
    def remember(self,identifier,text,source,created_utc=None):
        record=validate_record({"id":identifier,"text":text,"source":source,
            "created_utc":created_utc or datetime.now(timezone.utc).isoformat()})
        records=self.read()
        if any(x["id"]==identifier for x in records):
            raise ValueError("DUPLICATE_ID")
        if len(records)>=MAX_ITEMS:
            raise ValueError("MEMORY_FULL")
        self._write(records+[record])
        return record
    def search(self,query):
        if not isinstance(query,str) or not query.strip():
            return []
        q=query.casefold()
        return [x for x in self.read() if q in x["text"].casefold() or q in x["source"].casefold()]
    def forget(self,identifier):
        records=self.read()
        remaining=[x for x in records if x["id"]!=identifier]
        if len(remaining)==len(records):
            return False
        self._write(remaining)
        return True
