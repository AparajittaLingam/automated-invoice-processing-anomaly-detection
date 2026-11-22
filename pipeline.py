from pathlib import Path
from decimal import Decimal
from datetime import date
import re,csv
BASE=Path(__file__).resolve().parent
AS_OF=date(2025,4,1)
def parse(text):
 result={}
 for key,label in [('vendor','Vendor'),('invoice_number','Invoice'),('date','Date'),('currency','Currency'),('quantity','Quantity'),('unit_price','Unit price'),('subtotal','Subtotal'),('tax','Tax'),('total','Total')]:
  match=re.search(r'^'+re.escape(label)+r':\s*(.+)$',text,re.M);result[key]=match.group(1).strip() if match else None
 return result
if __name__=='__main__':
 rows=[];seen={}
 for p in sorted((BASE/'text').glob('*.txt')):
  r=parse(p.read_text());reasons=[]
  if any(r[k] is None for k in ['vendor','invoice_number','date','currency','subtotal','tax','total']):reasons.append('missing_field')
  if all(r[k] is not None for k in ['subtotal','tax','total']):
   if abs(Decimal(r['subtotal'])+Decimal(r['tax'])-Decimal(r['total']))>Decimal('.01'):reasons.append('arithmetic_error')
  key=(r['vendor'],r['invoice_number'])
  if key in seen:reasons.append('duplicate')
  seen[key]=p.stem
  rows.append({'document_id':p.stem,'source_file':p.name,**r,'is_anomaly':int(bool(reasons)),'anomaly_reason':';'.join(reasons)})
 with (BASE/'extracted_records.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print('Saved extracted_records.csv. Baseline reads text counterparts; PDF/OCR student tasks.')
