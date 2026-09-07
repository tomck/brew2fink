import csv, json, shutil, subprocess
from pathlib import Path
from macpkg_migrate.core import Identity, candidates_for, dry_run, install_allowed, plan_record

def inventory(run=subprocess.run):
    data=json.loads(run(["brew","info","--json=v2","--installed"],capture_output=True,text=True,check=True).stdout)
    rows=[]
    for formula in data.get("formulae",[]):
        if any(x.get("installed_on_request") for x in formula.get("installed",[])):
            rows.append({"kind":"formula","name":formula.get("name") or formula.get("full_name")})
    rows.extend({"kind":"cask","name":c.get("token") or c.get("name")} for c in data.get("casks",[]))
    return rows

def plan(items, snapshot):
    """Build shared-core plan records with Fink-specific source identities."""
    rows = []
    relations = snapshot.get("relations", [])
    for item in items:
        source = Identity("homebrew", "formula" if item["kind"] == "formula" else "cask", item["name"])
        candidates = [candidate for candidate in candidates_for(relations, source) if candidate.target.manager == "fink"]
        record = plan_record(source, candidates, snapshot.get("catalog_version"), preference=("fink",))
        record["kind"] = item["kind"]
        record["homebrew"] = item["name"]
        rows.append(record)
    return rows

def write_csv(rows,path):
    with open(path,"w",newline="") as stream:
        writer=csv.writer(stream); writer.writerow(["kind","homebrew","recommended_fink","confidence","reason","review_status"])
        for row in rows:
            choice = row.get("recommendation") or {}
            writer.writerow([row["kind"], row["homebrew"], choice.get("name", ""), choice.get("confidence", ""), choice.get("method", ""), choice.get("review_status", "needs-review")])

def install(rows,apply=False,run=subprocess.run):
    result=[]
    for row in rows:
        choice = row.get("recommendation") or {}
        if not install_allowed(row):
            result.append({**dry_run(row), "status": "needs-review"})
            continue
        package = choice.get("target", {}).get("native_name")
        command=["fink","install",package]
        if not apply: result.append({**row,"status":"dry-run","command":command}); continue
        if not fink_target_exists(package, run):
            result.append({**row,"status":"target-missing","command":command,"rollback":"No package was changed; review the Fink target and plan."})
            continue
        outcome=run(command); result.append({**row,"status":"installed" if outcome.returncode==0 else "failed","command":command})
    return result

def update_fink(run=subprocess.run):
    fink=shutil.which("fink")
    if not fink: raise RuntimeError("Fink is not installed; install Fink before updating it")
    result=run([fink,"selfupdate"])
    if result.returncode: raise RuntimeError(f"Fink selfupdate failed with exit code {result.returncode}")
    return {"status":"updated","command":[fink,"selfupdate"]}

def fink_target_exists(package, run=subprocess.run):
    """Check that Fink knows the candidate before attempting installation."""
    outcome=run(["fink","list",package],capture_output=True,text=True)
    if outcome.returncode != 0:
        return False
    return any(line.split() and line.split()[0] == package for line in outcome.stdout.splitlines())

def verify(rows,run=subprocess.run):
    result=[]
    for row in rows:
        choice = row.get("recommendation") or {}
        package = choice.get("target", {}).get("native_name")
        if not package:
            result.append({"homebrew":row["homebrew"],"fink":None,"verified":False,"reason":"no mapping"}); continue
        result.append({"homebrew":row["homebrew"],"fink":package,"verified":fink_target_exists(package, run)})
    return result
