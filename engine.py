"""Synthetic P&C demo: no insurer production connections, regulatory layouts or LLM calls."""
import csv, io, json, sqlite3
from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher
DB=Path(__file__).parent/'demo.sqlite'
SCHEMA='''
CREATE TABLE IF NOT EXISTS policies(policy_id TEXT PRIMARY KEY, insured TEXT, state TEXT, product TEXT, coverage_a REAL, deductible REAL, zip TEXT, effective_date TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS coverages(policy_id TEXT, coverage TEXT, limit_amount REAL);
CREATE TABLE IF NOT EXISTS claims(claim_id TEXT PRIMARY KEY, policy_id TEXT, loss_type TEXT, incurred REAL, paid REAL, status TEXT);
CREATE TABLE IF NOT EXISTS billing(bill_id TEXT PRIMARY KEY, policy_id TEXT, due REAL, paid REAL);
CREATE TABLE IF NOT EXISTS elements(global_name TEXT PRIMARY KEY, definition TEXT, data_type TEXT, module TEXT, picklist TEXT);
CREATE TABLE IF NOT EXISTS aliases(source_system TEXT, source_field TEXT, global_name TEXT, status TEXT, PRIMARY KEY(source_system,source_field));
CREATE TABLE IF NOT EXISTS picklists(name TEXT, code TEXT, label TEXT, PRIMARY KEY(name,code));
CREATE TABLE IF NOT EXISTS rules(rule_id TEXT PRIMARY KEY, description TEXT, expression TEXT, severity TEXT, status TEXT, effective_date TEXT);
CREATE TABLE IF NOT EXISTS factors(factor_id TEXT PRIMARY KEY, category TEXT, factor REAL, effective_date TEXT);
CREATE TABLE IF NOT EXISTS forms(form_id TEXT PRIMARY KEY, description TEXT, condition TEXT, edition TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, at_utc TEXT, actor TEXT, action TEXT, target TEXT, details TEXT);
'''
POLICIES=[('FL-HO3-1001','Sample Household A','FL','HO3',400000,4000,'34293','2026-01-01','Active'),('FL-HO3-1002','Sample Household B','FL','HO3',500000,5000,'34285','2026-02-01','Active'),('FL-HO3-1003','Sample Household C','FL','HO3',350000,3500,'33101','2026-03-01','Active'),('FL-HO3-1004','Sample Household D','FL','HO3',600000,6000,'32801','2026-04-01','Active'),('FL-HO3-1005','Sample Household E','FL','HO3',300000,3000,'34102','2026-05-01','Cancelled')]
ELEMENTS=[('PolicyNumber','Unique identifier for a policy','TEXT','Policy',''),('CoverageA','Coverage A dwelling insurance limit','DECIMAL','Policy',''),('PolicyStatus','Current policy status','TEXT','Policy','PolicyStatus'),('State','US risk state code','TEXT','Policy','USState'),('Product','Insurance product code','TEXT','Policy','Product'),('Deductible','Selected policy deductible','DECIMAL','Rating',''),('ClaimNumber','Unique claim identifier','TEXT','Claims',''),('ClaimPaid','Claim payments to date','DECIMAL','Claims',''),('PremiumDue','Premium amount billed','DECIMAL','Billing',''),('PremiumPaid','Premium amount collected','DECIMAL','Billing',''),('EffectiveDate','Policy inception date','DATE','Policy','')]
ALIASES=[('LegacyCSV','POL_NO','PolicyNumber','Approved'),('LegacyCSV','COV_A','CoverageA','Approved'),('LegacyCSV','POL_STAT','PolicyStatus','Approved'),('GuidewireSample','PolicyNumber','PolicyNumber','Approved'),('DuckCreekSample','Policy_ID','PolicyNumber','Approved')]
RULES=[('R01','State must be FL','state == "FL"','Error','Approved','2026-01-01'),('R02','Product must be HO3','product == "HO3"','Error','Approved','2026-01-01'),('R03','Coverage A >= $100,000','coverage_a >= 100000','Error','Approved','2026-01-01'),('R04','Coverage A <= $1 million','coverage_a <= 1000000','Review','Approved','2026-01-01'),('R05','Deductible > 0','deductible > 0','Error','Approved','2026-01-01'),('R06','Deductible not above 10% of A','deductible <= coverage_a * 0.10','Review','Approved','2026-01-01'),('R07','ZIP has exactly five digits','len(zip) == 5 and zip.isdigit()','Error','Approved','2026-01-01'),('R08','Policy must be active for issuance','status == "Active"','Review','Approved','2026-01-01'),('R09','Coverage A at least $250,000','coverage_a >= 250000','Review','Approved','2026-01-01'),('R10','Deductible <= $10,000','deductible <= 10000','Review','Approved','2026-01-01')]
# All rule IDs are mapped to deterministic Python; expressions above are descriptive data, never eval-ed.
def rule_results(p):
 checks={'R01':p['state']=='FL','R02':p['product']=='HO3','R03':p['coverage_a']>=100000,'R04':p['coverage_a']<=1000000,'R05':p['deductible']>0,'R06':p['deductible']<=p['coverage_a']*.10,'R07':len(p['zip'])==5 and p['zip'].isdigit(),'R08':p['status']=='Active','R09':p['coverage_a']>=250000,'R10':p['deductible']<=10000}
 return [{'rule_id':r[0],'description':r[1],'result':'PASS' if checks[r[0]] else 'FAIL','severity':r[3]} for r in RULES]
def connect():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def audit(c, action,target,details='',actor='demo_user'):
 c.execute('INSERT INTO audit(at_utc,actor,action,target,details) VALUES(?,?,?,?,?)',(datetime.now(timezone.utc).isoformat(),actor,action,target,details));c.commit()
def initialize(reset=False):
 if reset and DB.exists():DB.unlink()
 with connect() as c:
  c.executescript(SCHEMA)
  if c.execute('SELECT COUNT(*) FROM policies').fetchone()[0]:return
  for t,rows in [('policies',POLICIES),('elements',ELEMENTS),('aliases',ALIASES),('rules',RULES)]:
   fields={'policies':'policy_id,insured,state,product,coverage_a,deductible,zip,effective_date,status','elements':'global_name,definition,data_type,module,picklist','aliases':'source_system,source_field,global_name,status','rules':'rule_id,description,expression,severity,status,effective_date'}[t]
   c.executemany(f'INSERT INTO {t}({fields}) VALUES({",".join("?" for _ in rows[0])})',rows)
  c.executemany('INSERT INTO picklists VALUES (?,?,?)',[('PolicyStatus','Active','Active'),('PolicyStatus','Cancelled','Cancelled'),('USState','FL','Florida'),('Product','HO3','Homeowners Form 3')])
  c.executemany('INSERT INTO factors VALUES (?,?,?,?)',[('BASE_RATE','per_1000_coverage_a',3.5,'2026-01-01'),('WIND_FACTOR','multiplicative',1.2,'2026-01-01'),('POLICY_FEE','flat',35,'2026-01-01')])
  c.executemany('INSERT INTO forms VALUES (?,?,?,?)',[('DEMO-HO3-BASE','Synthetic HO3 base form','All active HO3','2026-01'),('DEMO-FL-WIND','Synthetic Florida wind notice','FL active HO3','2026-01')])
  c.executemany('INSERT INTO coverages VALUES (?,?,?)',[(p[0],'A-Dwelling',p[4]) for p in POLICIES]+[(p[0],'C-Personal Property',p[4]*.5) for p in POLICIES])
  c.executemany('INSERT INTO claims VALUES (?,?,?,?,?,?)',[('CL-001','FL-HO3-1001','Wind',12000,6000,'Open'),('CL-002','FL-HO3-1002','Water',8000,8000,'Closed')])
  c.executemany('INSERT INTO billing VALUES (?,?,?,?)',[('B-001','FL-HO3-1001',1715,1715),('B-002','FL-HO3-1002',2135,1000),('B-003','FL-HO3-1003',1505,1505)])
  c.commit();audit(c,'INIT','demo','Created synthetic seed data')
def rows(table):
 allowed={'policies','coverages','claims','billing','elements','aliases','picklists','rules','factors','forms','audit'}
 if table not in allowed:raise ValueError('Unapproved table')
 with connect() as c:return [dict(x) for x in c.execute(f'SELECT * FROM {table}').fetchall()]
def rate(p):
 base=round(p['coverage_a']/1000*3.5,2);wind=round(base*.2,2);fee=35
 return {'base':base,'wind':wind,'fee':fee,'premium':round(base+wind+fee,2),'forms':['DEMO-HO3-BASE','DEMO-FL-WIND'] if p['status']=='Active' else []}
def suggest(field):
 choices=[x['global_name'] for x in rows('elements')];return sorted([{'canonical':n,'score':round(SequenceMatcher(None,field.lower().replace('_',''),n.lower()).ratio(),2)} for n in choices],key=lambda x:x['score'],reverse=True)[:3]
def approve_alias(system,field,canonical):
 with connect() as c:
  if not c.execute('SELECT 1 FROM elements WHERE global_name=?',(canonical,)).fetchone():raise ValueError('Unknown canonical data element')
  c.execute('INSERT INTO aliases VALUES(?,?,?,?) ON CONFLICT(source_system,source_field) DO UPDATE SET global_name=excluded.global_name,status=excluded.status',(system,field,canonical,'Approved'));c.commit();audit(c,'APPROVE_MAPPING',system+':'+field,canonical)
def bureau_csv():
 """SYNTHETIC educational layout, never regulatory compliant."""
 buffer=io.StringIO();w=csv.writer(buffer);w.writerow(['DEMO_ONLY_POLICY_ID','DEMO_STATE','DEMO_PRODUCT','DEMO_COVERAGE_A','DEMO_PREMIUM','DEMO_EFFECTIVE_DATE'])
 for p in rows('policies'):
  if p['status']=='Active':w.writerow([p['policy_id'],p['state'],p['product'],p['coverage_a'],rate(p)['premium'],p['effective_date']])
 return buffer.getvalue()
def validation():
 out=[]
 for p in rows('policies'):
  for r in rule_results(p):
   if r['result']=='FAIL':out.append({'policy_id':p['policy_id'],'issue':r['description'],'severity':r['severity']})
 for b in rows('billing'):
  if b['paid']>b['due']:out.append({'policy_id':b['policy_id'],'issue':'Payment exceeds due','severity':'Error'})
 return out
if __name__=='__main__':initialize();print('Initialized',DB)
