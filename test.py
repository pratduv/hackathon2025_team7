import time
import requests
from pathlib import Path
import uvicorn
from multiprocessing import Process

# ---- Launch app ----
def run_server():
    from main import app  # Adjust if your app file has a different name
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def wait_for_server(url, timeout=10):
    for _ in range(timeout * 10):
        try:
            requests.get(url)
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(0.1)
    return False

def main():
    # Start FastAPI server in a background process
    server = Process(target=run_server, daemon=True)
    server.start()

    # Wait for it to be up
    if not wait_for_server("http://127.0.0.1:8000/docs"):
        print("Server failed to start.")
        server.terminate()
        return

    print("[SERVER] Started.")

    # --- Clean up any existing regulations ---
    try:
        existing = requests.get("http://127.0.0.1:8000/get-regulations").json()
        for reg in existing:
            requests.delete("http://127.0.0.1:8000/delete-regulations", params={"regulation_id": reg["id"]})
        print("[CLEANUP] Existing regulations deleted.")
    except Exception as e:
        print(f"[CLEANUP ERROR] {e}")

    # --- Add Regulations ---
    regulations = [
        {
            "id": "GDPR-5",
            "description": "Ensure no personal data (e.g., names, emails, IPs) is logged or stored without masking"
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

    r = requests.post("http://127.0.0.1:8000/add-regulations", json=regulations)
    assert r.ok, f"Failed to add regulations: {r.status_code} - {r.text}"
    print("[ADD REGULATIONS] Success")

    # --- Check Violations ---
    test_file = Path(__file__).parent / "sample_bad.py"
    with open(test_file, "rb") as f:
        files = {"file": f}
        r = requests.post("http://127.0.0.1:8000/check-violations", files=files)

    if r.ok:
        result = r.json()
        print(f"\nChecked `{result['filename']}` ({result['total_lines']} lines), "
              f"found {result['total_violations']} violation(s):")
        for v in result["violations"]:
            print(f" - [{v['regulation_id']}] lines {v['start_line']}-{v['end_line']}: {v['description']} ({v['severity']})")
    else:
        print(f"[CHECK VIOLATIONS] Error {r.status_code}: {r.text}")

    # --- Shutdown ---
    print("[SERVER] Shutting down...")
    server.terminate()
    server.join()

if __name__ == "__main__":
    main()
