import re
import urllib.request
import sys
import os

def generate_image():
    md_path = os.path.join(os.getcwd(), 'check_in_sequence_diagram.md')
    output_path = os.path.join(os.getcwd(), 'check_in_sequence_diagram.png')
    
    print(f"Reading from: {md_path}")
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract mermaid code
        match = re.search(r'```mermaid\n(.*?)\n```', content, re.DOTALL)
        if not match:
            print("Error: No mermaid block found in markdown file.")
            # Try to see if the whole file is mermaid code if no block found
            if 'sequenceDiagram' in content:
                 mermaid_code = content
            else:
                 return

        mermaid_code = match.group(1) if match else content
        
        # Use kroki.io API (It's a reliable service for diagram generation)
        url = "https://kroki.io/mermaid/png"
        data = mermaid_code.encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'text/plain')
        
        print(f"Sending request to {url}...")
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    image_data = response.read()
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    print(f"Successfully generated image: {output_path}")
                    return
                else:
                    print(f"Failed to generate image with Kroki. Status: {response.status}")
        except Exception as e:
             print(f"Error connecting to kroki.io: {e}")
        
        # Fallback to mermaid.ink
        print("Trying fallback to mermaid.ink...")
        import base64
        code_bytes = mermaid_code.encode('utf-8')
        base64_bytes = base64.urlsafe_b64encode(code_bytes)
        base64_str = base64_bytes.decode('ascii')
        url = f"https://mermaid.ink/img/{base64_str}"
        
        print(f"Sending request to {url}...")
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    image_data = response.read()
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    print(f"Successfully generated image with mermaid.ink: {output_path}")
                else:
                    print(f"Failed with mermaid.ink. Status: {response.status}")
        except Exception as e:
            print(f"Error connecting to mermaid.ink: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generate_image()
