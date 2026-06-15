import os
import requests
import json

response = requests.get(
    "https://api.hubapi.com/crm/v3/pipelines/deals",
    headers={"Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}"}
)

data = response.json()

for pipeline in data["results"]:
    print(f"Pipeline: {pipeline['label']} (id: {pipeline['id']})")
    for stage in pipeline["stages"]:
        print(f"   Stage: {stage['label']:20s} -> id: {stage['id']}")