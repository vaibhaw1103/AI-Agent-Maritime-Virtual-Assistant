#!/usr/bin/env python3
"""
🔍 MARITIME ASSISTANT - DOCUMENT ANALYSIS TESTING SUITE
====================================================

Comprehensive testing of document analysis functionality:
- Document upload endpoints
- PDF text extraction
- Image OCR processing
- Maritime document analysis
- Chat with documents
- Error handling and edge cases

Version: 1.0
Date: August 22, 2025
"""

import requests
import json
import base64
import io
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class DocumentAnalysisTestSuite:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
    def log_result(self, test_name: str, passed: bool, response_time: float = 0, details: str = ""):
        """Log test results"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.results.append({
            "test": test_name,
            "status": status,
            "passed": passed,
            "response_time": response_time,
            "details": details
        })
        print(f"{status} - {test_name} ({response_time:.2f}s)")
        if details and not passed:
            print(f"   Details: {details}")

    def create_sample_maritime_document_image(self, document_type: str = "sof") -> str:
        """Create a sample maritime document image for testing"""
        try:
            # Create image with maritime document content
            width, height = 800, 600
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # Try to use a basic font
            try:
                font = ImageFont.truetype("arial.ttf", 16)
                title_font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
            
            if document_type == "sof":
                # Statement of Facts document
                title = "STATEMENT OF FACTS"
                content = [
                    "M.V. OCEAN STAR",
                    "IMO: 9123456",
                    "Port: ROTTERDAM",
                    "",
                    "NOR TENDERED: 08:00 hrs on 15 Aug 2025",
                    "BERTHED: 10:30 hrs on 15 Aug 2025", 
                    "COMMENCED LOADING: 12:00 hrs on 15 Aug 2025",
                    "COMPLETED LOADING: 18:00 hrs on 16 Aug 2025",
                    "",
                    "CARGO: CONTAINER",
                    "QUANTITY: 2,500 TEU",
                    "",
                    "WEATHER: FAIR",
                    "LAYTIME USED: 30 Hours",
                    "DEMURRAGE: USD 15,000 per day",
                    "",
                    "MASTER: CAPTAIN SMITH"
                ]
            elif document_type == "charter":
                # Charter Party document
                title = "CHARTER PARTY AGREEMENT"
                content = [
                    "VESSEL: M.V. MARITIME GLORY",
                    "OWNER: BLUE OCEAN SHIPPING LTD",
                    "CHARTERER: GLOBAL CARGO CORP",
                    "",
                    "LOAD PORT: SINGAPORE",
                    "DISCHARGE PORT: HAMBURG",
                    "",
                    "CARGO: STEEL COILS",
                    "QUANTITY: 25,000 MT",
                    "",
                    "FREIGHT RATE: USD 45.00 per MT",
                    "LAYTIME: 72 hours SHINC",
                    "DEMURRAGE: USD 25,000 per day",
                    "DESPATCH: USD 12,500 per day",
                    "",
                    "LAYCAN: 20-25 AUG 2025"
                ]
            else:
                # Bill of Lading
                title = "BILL OF LADING"
                content = [
                    "B/L NUMBER: MAEU123456789",
                    "VESSEL: M.V. CONTAINER STAR",
                    "",
                    "SHIPPER: EXPORT COMPANY LTD",
                    "CONSIGNEE: IMPORT TRADING INC",
                    "",
                    "PORT OF LOADING: SHANGHAI",
                    "PORT OF DISCHARGE: LOS ANGELES",
                    "",
                    "DESCRIPTION OF GOODS:",
                    "ELECTRONIC COMPONENTS",
                    "20 CONTAINERS FCL",
                    "",
                    "GROSS WEIGHT: 240,000 KG",
                    "FREIGHT PREPAID",
                    "",
                    "DATE: 20 AUG 2025"
                ]
            
            # Draw title
            draw.text((50, 30), title, fill='black', font=title_font)
            draw.line([(50, 60), (width-50, 60)], fill='black', width=2)
            
            # Draw content
            y_position = 80
            for line in content:
                draw.text((50, y_position), line, fill='black', font=font)
                y_position += 25
            
            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_base64
            
        except Exception as e:
            print(f"Error creating sample document: {e}")
            return ""

    def test_health_check(self):
        """Test if the server is running"""
        try:
            start_time = time.time()
            # Try the docs endpoint which should be available
            response = requests.get(f"{BASE_URL}/docs", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Health Check", True, response_time, "Server is running")
                return True
            else:
                # Fallback: try a simple endpoint that might exist
                try:
                    response = requests.get(f"{BASE_URL}/", timeout=5)
                    if response.status_code in [200, 404, 405]:  # Server responding
                        self.log_result("Health Check", True, response_time, "Server is running")
                        return True
                except:
                    pass
                self.log_result("Health Check", False, response_time, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Health Check", False, 0, f"Connection failed: {e}")
            return False

    def test_upload_document_endpoint(self):
        """Test the /upload endpoint with a mock file"""
        try:
            start_time = time.time()
            
            # Create a simple text file content
            file_content = "STATEMENT OF FACTS\\n\\nVessel: M.V. TEST SHIP\\nPort: ROTTERDAM\\nDemurrage: USD 20,000/day"
            
            # Prepare file upload
            files = {
                'file': ('test_document.txt', file_content, 'text/plain')
            }
            
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['document_id', 'extracted_text', 'key_insights', 'document_type']
                
                if all(field in data for field in required_fields):
                    self.log_result("Document Upload Endpoint", True, response_time, 
                                  f"Document ID: {data.get('document_id', 'N/A')}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Document Upload Endpoint", False, response_time, 
                                  f"Missing fields: {missing}")
            else:
                self.log_result("Document Upload Endpoint", False, response_time, 
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("Document Upload Endpoint", False, 0, f"Error: {e}")

    def test_upload_document_image_endpoint(self):
        """Test the /upload-document endpoint with image"""
        try:
            start_time = time.time()
            
            # Create a simple 100x100 white image with text
            image = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(image)
            draw.text((10, 10), "MARITIME DOCUMENT TEST", fill='black')
            draw.text((10, 50), "Charter Party Agreement", fill='black')
            draw.text((10, 90), "Freight: USD 50,000", fill='black')
            
            # Convert to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Prepare file upload
            files = {
                'file': ('test_document.png', buffer.getvalue(), 'image/png')
            }
            
            response = requests.post(f"{BASE_URL}/upload-document", files=files, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['document_id', 'filename', 'analysis', 'status']
                
                if all(field in data for field in required_fields):
                    self.log_result("Document Image Upload", True, response_time, 
                                  f"Status: {data.get('status', 'unknown')}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Document Image Upload", False, response_time, 
                                  f"Missing fields: {missing}")
            else:
                self.log_result("Document Image Upload", False, response_time, 
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("Document Image Upload", False, 0, f"Error: {e}")

    def test_chat_with_document_analysis(self):
        """Test the /chat/analyze-document endpoint"""
        try:
            start_time = time.time()
            
            # Create sample maritime document
            image_base64 = self.create_sample_maritime_document_image("sof")
            
            if not image_base64:
                self.log_result("Chat with Document", False, 0, "Failed to create sample document")
                return
            
            payload = {
                "query": "Analyze this Statement of Facts and tell me the demurrage amount",
                "image_data": image_base64,
                "file_type": "image",
                "conversation_id": "test_doc_analysis_001"
            }
            
            response = requests.post(f"{BASE_URL}/chat/analyze-document", 
                                   json=payload, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['response', 'conversation_id', 'timestamp']
                
                if all(field in data for field in required_fields):
                    response_text = data.get('response', '').lower()
                    # Check if response mentions demurrage or relevant maritime terms
                    maritime_terms = ['demurrage', 'usd', '15,000', 'statement', 'facts']
                    found_terms = [term for term in maritime_terms if term in response_text]
                    
                    if len(found_terms) >= 2:
                        self.log_result("Chat with Document Analysis", True, response_time, 
                                      f"Found maritime terms: {found_terms}")
                    else:
                        self.log_result("Chat with Document Analysis", False, response_time, 
                                      f"Response lacks maritime context: {response_text[:100]}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Chat with Document Analysis", False, response_time, 
                                  f"Missing fields: {missing}")
            else:
                self.log_result("Chat with Document Analysis", False, response_time, 
                              f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_result("Chat with Document Analysis", False, 0, f"Error: {e}")

    def test_different_document_types(self):
        """Test analysis of different maritime document types"""
        document_types = [
            ("Statement of Facts", "sof"),
            ("Charter Party", "charter"),
            ("Bill of Lading", "bl")
        ]
        
        for doc_name, doc_type in document_types:
            try:
                start_time = time.time()
                
                # Create specific document type
                image_base64 = self.create_sample_maritime_document_image(doc_type)
                
                if not image_base64:
                    self.log_result(f"Document Type: {doc_name}", False, 0, "Failed to create sample")
                    continue
                
                payload = {
                    "query": f"What type of maritime document is this?",
                    "image_data": image_base64,
                    "file_type": "image"
                }
                
                response = requests.post(f"{BASE_URL}/chat/analyze-document", 
                                       json=payload, timeout=TEST_TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '').lower()
                    
                    # Check if the document type is correctly identified
                    type_keywords = {
                        "sof": ["statement of facts", "sof", "laytime", "demurrage"],
                        "charter": ["charter party", "charter", "freight", "laycan"],
                        "bl": ["bill of lading", "b/l", "shipper", "consignee"]
                    }
                    
                    expected_keywords = type_keywords.get(doc_type, [])
                    found_keywords = [kw for kw in expected_keywords if kw in response_text]
                    
                    if found_keywords:
                        self.log_result(f"Document Type: {doc_name}", True, response_time, 
                                      f"Identified keywords: {found_keywords}")
                    else:
                        self.log_result(f"Document Type: {doc_name}", False, response_time, 
                                      f"Failed to identify document type in: {response_text[:100]}")
                else:
                    self.log_result(f"Document Type: {doc_name}", False, response_time, 
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Document Type: {doc_name}", False, 0, f"Error: {e}")

    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        
        # Test 1: Empty document
        try:
            start_time = time.time()
            payload = {
                "query": "Analyze this document",
                "image_data": "",
                "file_type": "image"
            }
            
            response = requests.post(f"{BASE_URL}/chat/analyze-document", 
                                   json=payload, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            # Should still work (fallback to regular chat)
            if response.status_code == 200:
                self.log_result("Error Handling - Empty Document", True, response_time, 
                              "Gracefully handled empty document")
            else:
                self.log_result("Error Handling - Empty Document", False, response_time, 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Error Handling - Empty Document", False, 0, f"Error: {e}")

        # Test 2: Invalid file type
        try:
            start_time = time.time()
            files = {
                'file': ('test.exe', b'invalid content', 'application/x-executable')
            }
            
            response = requests.post(f"{BASE_URL}/upload-document", files=files, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            # Should return error for non-image files
            if response.status_code == 400:
                self.log_result("Error Handling - Invalid File Type", True, response_time, 
                              "Correctly rejected non-image file")
            else:
                self.log_result("Error Handling - Invalid File Type", False, response_time, 
                              f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Error Handling - Invalid File Type", False, 0, f"Error: {e}")

    def test_performance_benchmarks(self):
        """Test performance with different document sizes"""
        try:
            # Test with larger document
            start_time = time.time()
            
            # Create a larger document image
            image = Image.new('RGB', (1200, 800), color='white')
            draw = ImageDraw.Draw(image)
            
            # Add lots of text to simulate real document
            y_pos = 20
            for i in range(40):
                draw.text((20, y_pos), f"Line {i+1}: This is sample maritime document content with various terms", fill='black')
                y_pos += 20
            
            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            payload = {
                "query": "Summarize this document",
                "image_data": image_base64,
                "file_type": "image"
            }
            
            response = requests.post(f"{BASE_URL}/chat/analyze-document", 
                                   json=payload, timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                if response_time < 10:  # Should process within 10 seconds
                    self.log_result("Performance - Large Document", True, response_time, 
                                  f"Processed large document in {response_time:.2f}s")
                else:
                    self.log_result("Performance - Large Document", False, response_time, 
                                  f"Too slow: {response_time:.2f}s")
            else:
                self.log_result("Performance - Large Document", False, response_time, 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Performance - Large Document", False, 0, f"Error: {e}")

    def print_summary(self):
        """Print comprehensive test results summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        failed_tests = total_tests - passed_tests
        total_time = time.time() - self.start_time
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print("\\n" + "="*80)
        print("🔍 DOCUMENT ANALYSIS FUNCTIONALITY TEST RESULTS")
        print("="*80)
        
        print(f"📊 SUMMARY:")
        print(f"   ✅ Passed: {passed_tests}/{total_tests}")
        print(f"   ❌ Failed: {failed_tests}/{total_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"   ⏱️  Total Time: {total_time:.2f}s")
        print(f"   ⚡ Avg Response: {avg_response_time:.2f}s")
        
        print("\\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.results, 1):
            print(f"   {i:2d}. {result['status']} - {result['test']} ({result['response_time']:.2f}s)")
            if result['details']:
                print(f"       → {result['details']}")
        
        print("\\n🔧 TESTED FUNCTIONALITY:")
        print("   • Document upload endpoints (/upload, /upload-document)")
        print("   • Chat with document analysis (/chat/analyze-document)")  
        print("   • Multiple document types (SOF, Charter Party, B/L)")
        print("   • Error handling (invalid files, empty documents)")
        print("   • Performance benchmarks (large documents)")
        print("   • API response structure validation")
        
        if passed_tests == total_tests:
            print("\\n🎉 RESULT: DOCUMENT ANALYSIS FUNCTIONALITY IS PERFECT! 🎉")
        elif passed_tests >= total_tests * 0.8:
            print("\\n✅ RESULT: DOCUMENT ANALYSIS FUNCTIONALITY IS MOSTLY WORKING")
        else:
            print("\\n⚠️ RESULT: DOCUMENT ANALYSIS NEEDS ATTENTION")
        
        print("="*80)

def main():
    print("🔍 MARITIME ASSISTANT - DOCUMENT ANALYSIS TESTING")
    print("=" * 60)
    print("Testing comprehensive document analysis functionality...")
    print(f"Target: {BASE_URL}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("=" * 60)
    
    suite = DocumentAnalysisTestSuite()
    
    # Run all tests
    if suite.test_health_check():
        suite.test_upload_document_endpoint()
        suite.test_upload_document_image_endpoint()
        suite.test_chat_with_document_analysis()
        suite.test_different_document_types()
        suite.test_error_handling()
        suite.test_performance_benchmarks()
    else:
        print("❌ Server not responding. Please start the backend server first.")
        return
    
    # Print comprehensive summary
    suite.print_summary()

if __name__ == "__main__":
    main()
