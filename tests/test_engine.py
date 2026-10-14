import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine

def test_seed_and_outputs(tmp_path):
 engine.DB=tmp_path/'test.sqlite';engine.initialize()
 assert len(engine.rows('policies'))==5
 assert len(engine.rows('rules'))==10
 assert engine.rate(engine.rows('policies')[0])['premium']==1715.0
 assert len(engine.bureau_csv().splitlines())==5
 assert engine.validation()
 engine.approve_alias('TEST','COV_AA','CoverageA')
 assert any(x['source_field']=='COV_AA' for x in engine.rows('aliases'))
 assert any(x['action']=='APPROVE_MAPPING' for x in engine.rows('audit'))
