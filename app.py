import streamlit as st
import pandas as pd
from engine import initialize,rows,rate,rule_results,suggest,approve_alias,bureau_csv,validation,connect,audit
initialize()
st.set_page_config(page_title='Neurology Insurance SuperAI-OS',page_icon='🧠',layout='wide')
st.title('🧠 Neurology Insurance SuperAI-OS')
st.caption('Integrated synthetic P&C proof of concept • Florida HO3 • No insurer connections • No live AI/API calls')
page=st.sidebar.radio('Engine',['Orchestration Dashboard','Canonical Data Hub','Business Rules Engine','Rating & Forms Engine','Bureau Reporting Engine','AI-Assisted Mapping','Validation & Audit'])
policies=rows('policies');chosen=st.sidebar.selectbox('Sample policy',[p['policy_id'] for p in policies]);p=next(x for x in policies if x['policy_id']==chosen)
if page=='Orchestration Dashboard':
 st.subheader('One governed flow across six engines')
 a,b,c=st.columns(3);a.metric('Policies',len(policies));b.metric('Rules',len(rows('rules')));c.metric('Validation exceptions',len(validation()))
 st.dataframe(pd.DataFrame(policies),hide_index=True,use_container_width=True)
 if st.button('Run integrated demo'):
  with connect() as cx:audit(cx,'RUN_ORCHESTRATOR',chosen,'Rule/rate/bureau/validation dry run')
  st.success('Orchestration run completed (simulation — no external transactions).')
  st.write({'selected_policy':chosen,'premium':rate(p)['premium'],'passed_rules':sum(r['result']=='PASS' for r in rule_results(p)),'total_rules':10,'exceptions':len(validation()),'bureau_records':len([x for x in policies if x['status']=='Active'])})
elif page=='Canonical Data Hub':
 st.subheader('Canonical tables, values and relationships')
 table=st.selectbox('Data catalog',['elements','aliases','picklists','policies','coverages','claims','billing']);st.dataframe(pd.DataFrame(rows(table)),hide_index=True,use_container_width=True)
 st.info('Canonical data is inspectable. Mapping approvals are editable in AI-Assisted Mapping.')
elif page=='Business Rules Engine':
 st.subheader('Deterministic rules workbench');st.dataframe(pd.DataFrame(rows('rules')),hide_index=True,use_container_width=True)
 if st.button('Execute 10 approved rules'):
  results=rule_results(p);st.dataframe(pd.DataFrame(results),hide_index=True,use_container_width=True)
  with connect() as cx:audit(cx,'EXECUTE_RULES',chosen,f'{sum(x["result"]=="PASS" for x in results)}/10 pass')
 st.caption('Rule expressions shown for explainability. Approved rule IDs use explicitly coded Python logic; no eval or AI-generated code execution.')
elif page=='Rating & Forms Engine':
 st.subheader('Simplified HO3 rating demonstration')
 r=rate(p);a,b,c=st.columns(3);a.metric('Base',f'${r["base"]:,.2f}');b.metric('Wind',f'${r["wind"]:,.2f}');c.metric('Total demo premium',f'${r["premium"]:,.2f}')
 st.dataframe(pd.DataFrame(rows('factors')),hide_index=True);st.dataframe(pd.DataFrame(rows('forms')),hide_index=True)
 st.write('Applicable synthetic forms:',r['forms']);st.warning('Illustrative factors only — NOT approved rates, filed forms, actuarial indications or quotations.')
elif page=='Bureau Reporting Engine':
 st.subheader('Synthetic statistical reporting export')
 st.dataframe(pd.DataFrame([{'policy':x['policy_id'],'premium':rate(x)['premium']} for x in policies if x['status']=='Active']),hide_index=True)
 st.download_button('Download synthetic demonstration CSV',bureau_csv(),'DEMO_ONLY_bureau_report.csv','text/csv')
 st.warning('NOT an ISO/NCCI/AAIS/state filing layout. No actual bureau submission or certification.')
elif page=='AI-Assisted Mapping':
 st.subheader('Semantic mapping suggestions + explicit SME approval')
 field=st.text_input('Incoming source field','Policy_ID');system=st.text_input('Source identifier','SyntheticClient')
 suggestions=suggest(field);st.dataframe(pd.DataFrame(suggestions),hide_index=True)
 pick=st.selectbox('SME approved canonical target',[x['global_name'] for x in rows('elements')],index=0)
 if st.button('Approve mapping'):
  approve_alias(system,field,pick);st.success('Mapping stored with approval status and audit event.')
 st.caption('String-similarity assistance, not a connected LLM; proposed mappings must be checked for semantic equivalence.')
elif page=='Validation & Audit':
 st.subheader('Data-quality and workflow validation')
 st.dataframe(pd.DataFrame(validation()) if validation() else pd.DataFrame([{'result':'No exceptions'}]),hide_index=True)
 st.subheader('Audit event history');st.dataframe(pd.DataFrame(rows('audit')).sort_values('id',ascending=False),hide_index=True,use_container_width=True)
if st.sidebar.button('Reset synthetic demo database'):
 initialize(reset=True);st.rerun()
