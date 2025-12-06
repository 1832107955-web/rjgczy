import base64
import requests

def test_mermaid_fetch():
    code = """
graph TD
    A[Client] --> B[Server]
    """
    # Mermaid ink expects base64 encoded string of the graph definition
    # But it often requires a specific format or JSON wrapper.
    # Let's try the simplest: base64 of the code.
    
    # Actually, mermaid.ink uses pako compression usually for shorter URLs, 
    # but supports base64.
    # Format: https://mermaid.ink/img/<base64>
    
    code_bytes = code.encode('utf-8')
    base64_bytes = base64.urlsafe_b64encode(code_bytes)
    base64_str = base64_bytes.decode('ascii')
    
    url = f"https://mermaid.ink/img/{base64_str}"
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Success! Image downloaded.")
            with open("test_chart.png", "wb") as f:
                f.write(response.content)
        else:
            print(f"Failed with status {response.status_code}")
            # Try with the JSON wrapper method if simple string fails
            # Some versions expect {"code": "..."}
            import json
            json_obj = {"code": code, "mermaid": {"theme": "default"}}
            json_str = json.dumps(json_obj)
            b64_json = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('ascii')
            url2 = f"https://mermaid.ink/img/{b64_json}"
            print(f"Trying JSON wrapper URL: {url2}")
            response2 = requests.get(url2)
            if response2.status_code == 200:
                print("Success with JSON wrapper!")
            else:
                print(f"Failed again: {response2.status_code}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mermaid_fetch()
