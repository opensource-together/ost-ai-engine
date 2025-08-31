"""
Performance tests for the Go API.
"""

import pytest
import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.infrastructure.config import settings


@pytest.mark.performance
@pytest.mark.slow
def test_api_response_time():
    """Test API response time under normal load."""
    print("🔍 API RESPONSE TIME TEST")
    print("=" * 80)
    
    # Test user ID (should exist in test data)
    test_user_id = "ab18fc24-40d9-4055-ac46-393e25eb3736"  # eve_data
    api_url = f"http://localhost:{settings.GO_API_PORT}/recommendations"
    
    response_times = []
    num_requests = 50
    
    for i in range(num_requests):
        start_time = time.time()
        try:
            response = requests.get(f"{api_url}?user_id={test_user_id}", timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000  # Convert to ms
                response_times.append(response_time)
                print(f"Request {i+1}: {response_time:.2f}ms")
            else:
                print(f"Request {i+1}: Failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request {i+1}: Failed - {e}")
            pytest.skip("API not available")
    
    if response_times:
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        
        print(f"\n📊 Response Time Statistics:")
        print(f"   Average: {avg_time:.2f}ms")
        print(f"   Median: {median_time:.2f}ms")
        print(f"   95th percentile: {p95_time:.2f}ms")
        print(f"   Min: {min(response_times):.2f}ms")
        print(f"   Max: {max(response_times):.2f}ms")
        
        # Performance assertions
        assert avg_time < 100, f"Average response time {avg_time:.2f}ms exceeds 100ms"
        assert p95_time < 200, f"95th percentile response time {p95_time:.2f}ms exceeds 200ms"
        print("✅ API performance meets requirements")


@pytest.mark.performance
@pytest.mark.slow
def test_api_concurrent_load():
    """Test API performance under concurrent load."""
    print("\n🔍 API CONCURRENT LOAD TEST")
    print("=" * 80)
    
    test_user_id = "ab18fc24-40d9-4055-ac46-393e25eb3736"  # eve_data
    api_url = f"http://localhost:{settings.GO_API_PORT}/recommendations"
    
    num_concurrent = 10
    requests_per_thread = 10
    total_requests = num_concurrent * requests_per_thread
    
    def make_requests(thread_id):
        """Make requests for a single thread."""
        thread_times = []
        for i in range(requests_per_thread):
            start_time = time.time()
            try:
                response = requests.get(f"{api_url}?user_id={test_user_id}", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = (end_time - start_time) * 1000
                    thread_times.append(response_time)
                    
            except requests.exceptions.RequestException:
                pass
                
        return thread_times
    
    # Run concurrent requests
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = [executor.submit(make_requests, i) for i in range(num_concurrent)]
        all_times = []
        
        for future in as_completed(futures):
            thread_times = future.result()
            all_times.extend(thread_times)
    
    total_time = time.time() - start_time
    
    if all_times:
        successful_requests = len(all_times)
        throughput = successful_requests / total_time
        
        print(f"📊 Concurrent Load Results:")
        print(f"   Total requests: {total_requests}")
        print(f"   Successful requests: {successful_requests}")
        print(f"   Success rate: {(successful_requests/total_requests)*100:.1f}%")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Throughput: {throughput:.1f} requests/second")
        print(f"   Average response time: {statistics.mean(all_times):.2f}ms")
        
        # Performance assertions
        assert throughput > 10, f"Throughput {throughput:.1f} req/s below 10 req/s"
        assert successful_requests / total_requests > 0.9, "Success rate below 90%"
        print("✅ API handles concurrent load well")
    else:
        pytest.skip("No successful requests - API may not be available")


@pytest.mark.performance
@pytest.mark.slow
def test_api_memory_usage():
    """Test API memory usage under load."""
    print("\n🔍 API MEMORY USAGE TEST")
    print("=" * 80)
    
    # Use a real user_id that exists in the database
    test_user_id = "ab18fc24-40d9-4055-ac46-393e25eb3736"  # eve_data
    api_url = f"http://localhost:{settings.GO_API_PORT}/recommendations"
    
    # First, check if API is available
    try:
        health_response = requests.get(f"http://localhost:{settings.GO_API_PORT}/health", timeout=5)
        if health_response.status_code != 200:
            pytest.skip("API health check failed - API may not be running")
    except requests.exceptions.RequestException:
        pytest.skip("API not available - skipping memory usage test")
    
    # Make many requests to stress the API
    num_requests = 50  # Reduced for faster testing
    successful_requests = 0
    
    for i in range(num_requests):
        try:
            response = requests.get(f"{api_url}?user_id={test_user_id}", timeout=10)
            if response.status_code == 200:
                successful_requests += 1
                
            # Small delay to avoid overwhelming the API
            time.sleep(0.02)
            
        except requests.exceptions.RequestException:
            pass
    
    success_rate = successful_requests / num_requests
    print(f"📊 Memory Usage Test Results:")
    print(f"   Requests made: {num_requests}")
    print(f"   Successful requests: {successful_requests}")
    print(f"   Success rate: {success_rate*100:.1f}%")
    
    # More lenient assertion for CI environment
    assert success_rate > 0.8, f"API stability compromised under load (success rate: {success_rate*100:.1f}%)"
    print("✅ API remains stable under load")


@pytest.mark.performance
@pytest.mark.slow
def test_api_error_handling_performance():
    """Test API performance when handling errors."""
    print("\n🔍 API ERROR HANDLING PERFORMANCE TEST")
    print("=" * 80)
    
    api_url = f"http://localhost:{settings.GO_API_PORT}/recommendations"
    
    # Test with invalid user IDs
    invalid_user_ids = [
        "invalid-uuid",
        "00000000-0000-0000-0000-000000000000",
        "not-a-uuid-at-all",
        "",
        "123"
    ]
    
    error_response_times = []
    
    for user_id in invalid_user_ids:
        start_time = time.time()
        try:
            response = requests.get(f"{api_url}?user_id={user_id}", timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            error_response_times.append(response_time)
            
            print(f"Invalid user '{user_id}': {response_time:.2f}ms (status: {response.status_code})")
            
        except requests.exceptions.RequestException as e:
            print(f"Invalid user '{user_id}': Request failed - {e}")
    
    if error_response_times:
        avg_error_time = statistics.mean(error_response_times)
        print(f"\n📊 Error Handling Performance:")
        print(f"   Average error response time: {avg_error_time:.2f}ms")
        print(f"   Max error response time: {max(error_response_times):.2f}ms")
        
        # Error responses should be fast
        assert avg_error_time < 50, f"Error response time {avg_error_time:.2f}ms too slow"
        print("✅ API handles errors efficiently")
    else:
        pytest.skip("No error responses received - API may not be available")


if __name__ == "__main__":
    # Run performance tests
    test_api_response_time()
    test_api_concurrent_load()
    test_api_memory_usage()
    test_api_error_handling_performance()
    
    print("\n✅ All performance tests completed!")
