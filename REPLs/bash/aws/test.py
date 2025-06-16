#!/usr/bin/env python3
import subprocess
import requests
import time
import base64
import json
import signal
import sys
import os

class SAMTestRunner:
    def __init__(self, port=3000):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.sam_process = None
    
    def start_sam_local(self):
        """Start SAM local API server"""
        print("Starting SAM local API server...")
        
        # Check if template.yaml exists, create basic one if not
        if not os.path.exists("template.yaml"):
            print("No template.yaml found, creating basic template...")
            self.create_basic_template()
        
        try:
            self.sam_process = subprocess.Popen([
                "sam", "local", "start-api", 
                "--port", str(self.port),
                "--host", "0.0.0.0"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            print("Waiting for SAM local to start...")
            for i in range(30):  # 30 second timeout
                try:
                    response = requests.get(f"{self.base_url}/api/health", timeout=2)
                    if response.status_code == 200:
                        print(f"SAM local started on port {self.port}")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
            
            print("Failed to start SAM local within 30 seconds")
            return False
            
        except Exception as e:
            print(f"Error starting SAM local: {e}")
            return False
    
    def create_basic_template(self):
        """Create a basic SAM template for the bash REPL"""
        template_content = """AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  BashReplFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: function.handler
      Runtime: provided.al2
      Events:
        Health:
          Type: Api
          Properties:
            Path: /api/health
            Method: GET
        Exec:
          Type: Api
          Properties:
            Path: /api/exec/{_src}
            Method: GET
"""
        
        with open("template.yaml", "w") as f:
            f.write(template_content)
        
        print("Created basic template.yaml")
    
    def test_health_endpoint(self):
        """Test the health endpoint"""
        print("\nTesting health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("Health check passed")
                return True
            else:
                print("Health check failed")
                return False
                
        except Exception as e:
            print(f"Health check error: {e}")
            return False
    
    def test_exec_endpoint(self):
        """Test the exec endpoint with sample bash code"""
        print("\nTesting exec endpoint...")
        
        # Test cases
        test_cases = [
            {
                "name": "Simple echo",
                "code": "echo 'Hello from bash REPL!'"
            },
            {
                "name": "Date command", 
                "code": "date"
            },
            {
                "name": "Environment check",
                "code": "echo $USER && pwd"
            },
            {
                "name": "Math calculation",
                "code": "echo $((2 + 2))"
            }
        ]
        
        results = []
        for test in test_cases:
            print(f"\nRunning test: {test['name']}")
            try:
                # Encode the bash code
                encoded_code = base64.b64encode(test['code'].encode()).decode()
                
                # Make request
                response = requests.get(
                    f"{self.base_url}/api/exec/{encoded_code}", 
                    timeout=15
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Output: {result.get('body', 'No output')}")
                    results.append({"test": test['name'], "status": "PASS", "output": result.get('body')})
                    print("Test passed")
                else:
                    print(f"Test failed with status {response.status_code}")
                    results.append({"test": test['name'], "status": "FAIL", "error": f"HTTP {response.status_code}"})
                    
            except Exception as e:
                print(f"Test error: {e}")
                results.append({"test": test['name'], "status": "ERROR", "error": str(e)})
        
        return results
    
    def print_summary(self, health_result, exec_results):
        """Print test summary"""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        print(f"Health Check: {'PASS' if health_result else 'FAIL'}")
        
        print(f"\nExec Tests:")
        passed = 0
        for result in exec_results:
            status = "PASS" if result['status'] == "PASS" else "FAIL"
            print(f"  {result['test']}: {result['status']}")
            if result['status'] == "PASS":
                passed += 1
        
        print(f"\nOverall: {passed}/{len(exec_results)} exec tests passed")
        print("="*50)
    
    def stop_sam_local(self):
        """Stop SAM local server"""
        if self.sam_process:
            print("\nStopping SAM local server...")
            self.sam_process.terminate()
            try:
                self.sam_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.sam_process.kill()
            print("SAM local stopped")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("Starting Bash REPL API Tests")
        print("="*50)
        
        # Start SAM local
        if not self.start_sam_local():
            return False
        
        try:
            # Run tests
            health_result = self.test_health_endpoint()
            exec_results = self.test_exec_endpoint()
            
            # Print summary
            self.print_summary(health_result, exec_results)
            
            return health_result and all(r['status'] == 'PASS' for r in exec_results)
            
        finally:
            self.stop_sam_local()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nInterrupted by user")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    runner = SAMTestRunner()
    success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)