import time
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_tier_test(tier_name, expected_limit, total_requests):
    print(f"\n--- Starting {tier_name.upper()} Tier AI Limit Test (Expect Limit: {expected_limit}) ---")
    headers = {"X-User-Tier": tier_name}
    
    success_count = 0
    blocked_count = 0
    
    for i in range(1, total_requests + 1):
        response = requests.post(f"{BASE_URL}/api/v1/ai/generate" if "/api/v1" in BASE_URL else f"{BASE_URL}/ai/generate", headers=headers)
        
        if response.status_code == 200:
            success_count += 1
            print(f"Req {i}:  Success 200")
        elif response.status_code == 429:
            blocked_count += 1
            print(f"Req {i}:  Blocked 429! JSON: {response.json()}")
            
        time.sleep(0.1) 
        
    print(f"\n Results for {tier_name.upper()}: Total Allowed = {success_count}, Total Blocked = {blocked_count}")

if __name__ == "__main__":
    # Test 1: Free Tier AI 
    run_tier_test(tier_name="free", expected_limit=5, total_requests=7)
    
    print("\n" + "="*50 + "\nWaiting 5 seconds before starting Paid Test...")
    time.sleep(5)
    
    # Test 2: Paid Tier AI (Limit is 30. We send 35. Expect 30 success, 5 blocked)
    run_tier_test(tier_name="", expected_limit=30, total_requests=35)