"""Publish web/ to the stack's Amplify Hosting app.

    python scripts/deploy_web.py                 # write web/config.js from the stack, then publish
    python scripts/deploy_web.py --config-only   # only write web/config.js, for a local preview
"""

import io
import json
import os
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import boto3

STACK, REGION = "surya-saathi", "ap-south-1"
WEB = Path(__file__).resolve().parents[1] / "web"

outputs = {
    o["OutputKey"]: o["OutputValue"]
    for o in boto3.client("cloudformation", region_name=REGION).describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]
}
# the Twilio sandbox number; set WA_JOIN to the sandbox's "join xxx-yyy" phrase to show it on the page
wa = {"number": "+1 415 523 8886", "join": os.environ.get("WA_JOIN", "")}
# local previews (scripts/serve_local.py) answer the API at /api; everywhere else uses the deployed one
api = json.dumps(outputs["ApiUrl"])
# the roof tracer's map key: public by design, limited to map tiles from this site's addresses
maps = {"region": REGION, "key": ""}
if outputs.get("MapKeyName"):
    maps["key"] = boto3.client("location", region_name=REGION).describe_key(KeyName=outputs["MapKeyName"])["Key"]
(WEB / "config.js").write_text(
    f'window.SURYA_API = ["localhost", "127.0.0.1"].includes(location.hostname) ? "/api" : {api};\n'
    f"window.SURYA_WA = {json.dumps(wa)};\n"
    f"window.SURYA_MAPS = {json.dumps(maps)};\n", encoding="utf-8")

if "--config-only" in sys.argv:
    print("wrote", WEB / "config.js")
    sys.exit(0)

archive = io.BytesIO()
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(WEB.rglob("*")):
        if f.is_file():
            z.write(f, f.relative_to(WEB).as_posix())

amplify = boto3.client("amplify", region_name=REGION)
app, branch = outputs["WebAppId"], "main"
job = amplify.create_deployment(appId=app, branchName=branch)
urllib.request.urlopen(urllib.request.Request(job["zipUploadUrl"], data=archive.getvalue(), method="PUT", headers={"Content-Type": "application/zip"}))
amplify.start_deployment(appId=app, branchName=branch, jobId=job["jobId"])

while (status := amplify.get_job(appId=app, branchName=branch, jobId=job["jobId"])["job"]["summary"]["status"]) in ("PENDING", "RUNNING"):
    time.sleep(3)
print(status, outputs["WebUrl"])
