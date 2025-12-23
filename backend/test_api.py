"""
Quick test script for the Disaster Intelligence API
Run this after starting the API with: python app.py
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health check endpoint"""
    print("="*60)
    print("TEST 1: Health Check")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed!")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API!")
        print("   Make sure API is running: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_single_prediction():
    """Test single prediction endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Single Prediction")
    print("="*60)
    
    test_cases = [
        ("Fire breaking out in downtown area!", True),
        ("Beautiful sunny day at the beach", False),
        ("Earthquake hits California, buildings collapsing!", True),
        ("Just had a great lunch with friends", False),
        ("Flood warning issued for coastal regions", True),
    ]
    
    passed = 0
    for tweet, expected_disaster in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/predict",
                json={"text": tweet},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                is_disaster = result.get("disaster_label", 0) == 1
                confidence = result.get("confidence_percentage", 0)
                
                status = "✅" if (is_disaster == expected_disaster) else "⚠️"
                print(f"{status} Tweet: {tweet[:50]}...")
                print(f"   Prediction: {result.get('disaster_text')}")
                print(f"   Confidence: {confidence}%")
                print(f"   Category: {result.get('category')}")
                print(f"   Severity: {result.get('severity')}")
                print()
                passed += 1
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error testing '{tweet[:30]}...': {e}")
    
    print(f"✅ {passed}/{len(test_cases)} predictions successful")
    return passed == len(test_cases)

def test_batch_prediction():
    """Test batch prediction endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Batch Prediction")
    print("="*60)
    
    tweets = [
        "Fire breaking out in downtown area!",
        "Beautiful sunny day at the beach",
        "Earthquake hits California!",
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/batch_predict",
            json={"tweets": tweets},
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Batch prediction successful!")
            print(f"   Processed: {result.get('count')} tweets")
            print(f"   Results:")
            for i, res in enumerate(result.get("results", []), 1):
                print(f"   {i}. {res.get('disaster_text')} ({res.get('confidence_percentage')}%)")
            return True
        else:
            print(f"❌ Batch prediction failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("DISASTER INTELLIGENCE API - TEST SUITE")
    print("="*60)
    print(f"Testing API at: {BASE_URL}")
    print("Make sure API is running: python app.py")
    print()
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    # Test 2: Single predictions
    results.append(("Single Prediction", test_single_prediction()))
    
    # Test 3: Batch prediction
    results.append(("Batch Prediction", test_batch_prediction()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    print("="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  Some tests failed. Check API is running correctly.")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)






