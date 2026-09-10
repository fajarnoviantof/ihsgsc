import argparse,json
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
TZ=ZoneInfo("Asia/Jakarta"); HISTORY_FILE=Path("history.json"); KEEP_DAYS=31
SCHEDULE_TO_SLOT={"5 9 * * 1-5":"09:00","5 10 * * 1-5":"10:00","5 11 * * 1-5":"11:00","5 13 * * 1-5":"13:00","5 14 * * 1-5":"14:00","5 15 * * 1-5":"15:00","5 16 * * 1-5":"16:00","5 17 * * 1-5":"17:00"}
def load(p):
 try:return json.loads(Path(p).read_text(encoding="utf8"))
 except:return None
def add(h,scanner,payload,slot,cron):
 if not payload:return
 ts=payload.get("generated_at") or payload.get("finished_at")
 if not ts:return
 date=str(ts)[:10]
 h[:]=[x for x in h if not(x.get("scanner")==scanner and x.get("slot")==slot and str(x.get("generated_at","")).startswith(date))]
 h.append({"scanner":scanner,"slot":slot,"cron":cron,"generated_at":ts,"candidates":payload.get("candidates",0),"total_tickers":payload.get("total_tickers",0),"processed":payload.get("processed",0),"errors":payload.get("errors",0),"duration_text":payload.get("duration_text"),"data":payload.get("data",[])})
def main():
 p=argparse.ArgumentParser();p.add_argument("--ob",default="skipped");p.add_argument("--macd",default="skipped");p.add_argument("--schedule",default="");p.add_argument("--slot",default="");a=p.parse_args();slot=a.slot or SCHEDULE_TO_SLOT.get(a.schedule,"");
 if not slot:return
 old=load(HISTORY_FILE) or {}; h=old.get("history",[]) if isinstance(old,dict) else []
 if a.ob=="success":add(h,"SMC OB",load("results.json"),slot,a.schedule)
 if a.macd=="success":add(h,"MACD",load("macd_results.json"),slot,a.schedule)
 cutoff=datetime.now(TZ)-timedelta(days=KEEP_DAYS);h=[x for x in h if str(x.get("generated_at",""))[:10] and datetime.strptime(str(x["generated_at"])[:19],"%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)>=cutoff];h.sort(key=lambda x:x.get("generated_at",""),reverse=True)
 HISTORY_FILE.write_text(json.dumps({"updated_at":datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),"keep_days":KEEP_DAYS,"slots":["09:00","10:00","11:00","13:00","14:00","15:00","16:00","17:00"],"history":h},ensure_ascii=False,indent=2),encoding="utf8")
if __name__=="__main__":main()
