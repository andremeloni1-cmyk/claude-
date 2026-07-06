import json, sys, shutil, tempfile, os
from pathlib import Path
import importlib.util

# copy the real data to a temp file
src = Path("market-analysis.json")
tmp = Path(tempfile.mkdtemp())/"ma.json"
shutil.copy(src, tmp)

os.environ["TWELVEDATA_API_KEY"]="TESTKEY"
os.environ["TD_THROTTLE"]="0"  # no sleeping in test
spec = importlib.util.spec_from_file_location("rp", "scripts/refresh_prices.py")
rp = importlib.util.module_from_spec(spec)
# point module at temp file by patching argv-derived DATA after load
sys.argv=["refresh_prices.py", str(tmp)]
spec.loader.exec_module(rp)

before = json.loads(src.read_text())

# Mock fetch_price: known price for CBA + NVDA + sp500; fail everything else (keep old)
calls=[]
def fake_fetch(symbol, exchange=None):
    calls.append((symbol,exchange))
    table={("CBA","ASX"):111.11, ("NVDA",None):205.5, ("GSPC",None):7600.0, ("AUD/USD",None):0.701}
    return table.get((symbol,exchange))
rp.fetch_price = fake_fetch

rc = rp.main()
after = json.loads(tmp.read_text())

def price(doc,t): return next(c["priceApprox"] for c in doc["companies"] if c["ticker"]==t)
print("return code:", rc)
print("CBA  before->after:", price(before,"CBA"), "->", price(after,"CBA"), "(expect 111.11)")
print("NVDA before->after:", price(before,"NVDA"),"->", price(after,"NVDA"),"(expect 205.5)")
print("CSL  before->after:", price(before,"CSL"), "->", price(after,"CSL"), "(expect unchanged/kept)")
print("sp500 level:", after["marketSnapshot"]["sp500"]["level"], "(expect 7600.0)")
print("asx200 level:", after["marketSnapshot"]["asx200"]["level"], "(kept, XJO mocked as fail)")
print("audUsd:", after["marketSnapshot"]["audUsd"], "(expect 0.701)")
print("asOf updated:", after["asOf"] != "PLACEHOLDER", "->", after["asOf"])
print("qualitative intact — CSL thesis unchanged:", price and after["companies"][1]["thesis"]==before["companies"][1]["thesis"])
print("valid JSON + trailing newline:", tmp.read_text().endswith("}\n"))
print("total fetch calls:", len(calls))
