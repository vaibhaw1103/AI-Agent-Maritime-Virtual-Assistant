#!/usr/bin/env python3
"""
Test AI Chat Assistant functionality
"""

import requests
import json
import time

def test_chat_assistant():
    """Test the AI chat assistant with various maritime queries"""
    
    print('🤖 Testing AI Chat Assistant...')
    print('=' * 40)

    base_url = 'http://127.0.0.1:8000'
    
    # Test queries for maritime assistant
    test_queries = [
        {
            'query': 'Hello, what can you help me with?',
            'description': 'Basic greeting test'
        },
        {
            'query': 'What is the weather like in Singapore port?',
            'description': 'Port weather query test'
        },
        {
            'query': 'Tell me about container shipping',
            'description': 'Maritime knowledge test'
        },
        {
            'query': 'What are the largest ports in the world?',
            'description': 'Port information test'
        },
        {
            'query': 'How do I calculate shipping costs from Shanghai to Rotterdam?',
            'description': 'Logistics calculation test'
        },
        {
            'query': 'What documents do I need for international shipping?',
            'description': 'Documentation query test'
        }
    ]

    results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f'\n🔍 Test {i}: {test["description"]}')
        print(f'📝 Query: "{test["query"]}"')
        
        try:
            # Test the chat endpoint
            payload = {
                'query': test['query'],
                'conversation_id': f'test-conversation-{i}'
            }
            
            start_time = time.time()
            response = requests.post(f'{base_url}/chat', 
                                   json=payload,
                                   headers={'Content-Type': 'application/json'},
                                   timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f'✅ Status: {response.status_code}')
                print(f'⏱️ Response time: {response_time:.2f}s')
                
                # Check response structure
                if 'response' in data:
                    response_text = data['response']
                    print(f'📄 Response length: {len(response_text)} characters')
                    print(f'🎯 Response preview: {response_text[:150]}...')
                    
                    results.append({
                        'test': test['description'],
                        'status': 'PASS',
                        'response_time': response_time,
                        'response_length': len(response_text)
                    })
                else:
                    print('❌ Missing "response" field in JSON')
                    results.append({
                        'test': test['description'],
                        'status': 'FAIL - Missing response field',
                        'error': 'No response field'
                    })
                    
            else:
                print(f'❌ HTTP Error: {response.status_code}')
                error_text = response.text[:200] if response.text else 'No error message'
                print(f'🔍 Error details: {error_text}')
                
                results.append({
                    'test': test['description'],
                    'status': f'FAIL - HTTP {response.status_code}',
                    'error': error_text
                })
                
        except requests.exceptions.ConnectionError:
            print('❌ Connection Error: Backend server not running')
            results.append({
                'test': test['description'],
                'status': 'FAIL - Connection Error',
                'error': 'Backend server not running'
            })
            break
            
        except requests.exceptions.Timeout:
            print('❌ Timeout: Request took longer than 30 seconds')
            results.append({
                'test': test['description'],
                'status': 'FAIL - Timeout',
                'error': 'Request timeout'
            })
            
        except Exception as e:
            print(f'❌ Unexpected Error: {str(e)}')
            results.append({
                'test': test['description'],
                'status': 'FAIL - Exception',
                'error': str(e)
            })
        
        # Small delay between tests
        time.sleep(1)
    
    # Print summary
    print('\n' + '=' * 50)
    print('📊 AI CHAT ASSISTANT TEST SUMMARY')
    print('=' * 50)
    
    passed_tests = [r for r in results if r['status'] == 'PASS']
    failed_tests = [r for r in results if r['status'] != 'PASS']
    
    print(f'✅ Passed: {len(passed_tests)}/{len(results)} tests')
    print(f'❌ Failed: {len(failed_tests)}/{len(results)} tests')
    
    if passed_tests:
        avg_response_time = sum(r['response_time'] for r in passed_tests) / len(passed_tests)
        print(f'⏱️ Average response time: {avg_response_time:.2f}s')
        avg_response_length = sum(r['response_length'] for r in passed_tests) / len(passed_tests)
        print(f'📄 Average response length: {avg_response_length:.0f} characters')
    
    if failed_tests:
        print(f'\n❌ Failed Tests:')
        for test in failed_tests:
            print(f'  - {test["test"]}: {test["status"]}')
            if 'error' in test:
                print(f'    Error: {test["error"]}')
    
    return len(failed_tests) == 0

def test_chat_endpoint_structure():
    """Test the chat endpoint structure and requirements"""
    
    print('\n🔍 Testing Chat Endpoint Structure...')
    
    base_url = 'http://127.0.0.1:8000'
    
    # Test missing query field
    try:
        response = requests.post(f'{base_url}/chat', json={})
        print(f'📝 Empty payload test: {response.status_code}')
        if response.status_code != 200:
            print(f'   Response: {response.text[:100]}')
    except Exception as e:
        print(f'❌ Empty payload error: {e}')
    
    # Test malformed JSON
    try:
        response = requests.post(f'{base_url}/chat', 
                               data='{"invalid": json}',
                               headers={'Content-Type': 'application/json'})
        print(f'📝 Invalid JSON test: {response.status_code}')
    except Exception as e:
        print(f'❌ Invalid JSON error: {e}')

if __name__ == "__main__":
    success = test_chat_assistant()
    test_chat_endpoint_structure()
    
    if success:
        print('\n🎉 AI Chat Assistant is working correctly!')
    else:
        print('\n⚠️ AI Chat Assistant has issues that need fixing!')
