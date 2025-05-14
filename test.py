import json
import requests

# 1. Endpoint URL
url = "http://localhost:8000/check-regulations"

# 2. Prepare the file to upload
import os

# Get the current script's directory and use a relative path
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "sample_bad.py")
files = {
    "file": open(file_path, "rb")
}

# 3. Define your regulations as a JSON array
regulations = [
    {
        "id": "GDPR-5",
        "description": "Ensure  no personal data (e.g., names, emails, IPs) is logged or stored without masking"
    },
    {
        "id": "SOC2-CC6.1",
        "description": "All external API calls must use TLS/HTTPS"
    },
    {
        "id": "GDPR-17",
        "description": "Support right-to-be-forgotten: code must allow deletion of user data upon request"
    }
]

data = {
    # Must be a string — the server will `json.loads` it
    "regulations": json.dumps(regulations)
}

# 4. POST the request
response = requests.post(url, files=files, data=data)

# 5. Check and print the result
if response.ok:
    result = response.json()
    print(f"Checked `{result['filename']}` ({result['total_lines']} lines), "
          f"found {result['total_violations']} violation(s):")
    for v in result["violations"]:
        print(f" - [{v['regulation_id']}] lines {v['start_line']}-{v['end_line']}: {v['description']} ({v['severity']})")
else:
    print(f"Error {response.status_code}: {response.text}")