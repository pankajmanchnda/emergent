import requests
import sys
import json
from datetime import datetime, timezone

class NewsAPITester:
    def __init__(self, base_url="https://news-digest-dash.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_news_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        if params:
            print(f"   Params: {params}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_create_news_item(self, title, url, source, tags, item_type="rss", summary=None):
        """Test creating a news item"""
        data = {
            "title": title,
            "url": url,
            "source": source,
            "tags": tags,
            "item_type": item_type
        }
        if summary:
            data["summary"] = summary
            
        success, response = self.run_test(
            f"Create News Item - {title[:30]}...",
            "POST",
            "news",
            200,
            data=data
        )
        
        if success and 'id' in response:
            self.created_news_ids.append(response['id'])
            return response['id']
        return None

    def test_get_all_news(self):
        """Test getting all news items"""
        success, response = self.run_test(
            "Get All News Items",
            "GET",
            "news",
            200
        )
        
        if success:
            print(f"   Found {len(response)} news items")
            # Check if items are sorted by published_at descending
            if len(response) > 1:
                dates = [item.get('published_at') for item in response if item.get('published_at')]
                if len(dates) > 1:
                    sorted_check = all(dates[i] >= dates[i+1] for i in range(len(dates)-1))
                    print(f"   Sorted by date (newest first): {sorted_check}")
        
        return success, response if success else []

    def test_filter_by_tag(self, tag):
        """Test filtering news by tag"""
        success, response = self.run_test(
            f"Filter News by Tag: {tag}",
            "GET",
            "news",
            200,
            params={"tag": tag}
        )
        
        if success:
            print(f"   Found {len(response)} items with tag '{tag}'")
            # Verify all items have the tag (case-insensitive)
            tag_check = all(
                any(t.lower() == tag.lower() for t in item.get('tags', []))
                for item in response
            )
            print(f"   All items have tag '{tag}': {tag_check}")
        
        return success, response if success else []

    def test_case_insensitive_filter(self):
        """Test case-insensitive tag filtering"""
        # Test with different cases
        test_cases = ['iran', 'IRAN', 'Iran']
        results = []
        
        for case in test_cases:
            success, response = self.run_test(
                f"Case-insensitive filter: {case}",
                "GET",
                "news",
                200,
                params={"tag": case}
            )
            if success:
                results.append(len(response))
        
        # All should return the same number of results
        if results and all(count == results[0] for count in results):
            print("✅ Case-insensitive filtering works correctly")
            return True
        else:
            print("❌ Case-insensitive filtering failed")
            return False

    def test_delete_news_item(self, news_id):
        """Test deleting a news item"""
        success, response = self.run_test(
            f"Delete News Item: {news_id}",
            "DELETE",
            f"news/{news_id}",
            200
        )
        return success

    def cleanup_created_items(self):
        """Clean up any news items created during testing"""
        print(f"\n🧹 Cleaning up {len(self.created_news_ids)} created items...")
        for news_id in self.created_news_ids:
            self.test_delete_news_item(news_id)

def main():
    print("🚀 Starting Iran War Monitor API Tests")
    print("=" * 50)
    
    # Setup
    tester = NewsAPITester()
    
    # Test 1: Root endpoint
    tester.test_root_endpoint()
    
    # Test 2: Create sample news items
    print("\n📝 Creating test news items...")
    
    test_items = [
        {
            "title": "Iran Nuclear Program Update",
            "url": "https://example.com/iran-nuclear-1",
            "source": "Reuters",
            "tags": ["Iran", "Nuclear"],
            "summary": "Latest developments in Iran's nuclear program"
        },
        {
            "title": "Diplomatic Talks Resume",
            "url": "https://example.com/diplomacy-1",
            "source": "BBC",
            "tags": ["Diplomacy", "Iran"],
            "summary": "International diplomatic efforts continue"
        },
        {
            "title": "Regional War Tensions",
            "url": "https://example.com/war-1",
            "source": "CNN",
            "tags": ["War", "Iran"],
            "summary": "Analysis of regional military tensions"
        },
        {
            "title": "YouTube Analysis Video",
            "url": "https://youtube.com/watch?v=test",
            "source": "Military Analysis Channel",
            "tags": ["War", "Nuclear"],
            "item_type": "youtube",
            "summary": "Expert analysis on current situation"
        }
    ]
    
    created_ids = []
    for item in test_items:
        item_id = tester.test_create_news_item(**item)
        if item_id:
            created_ids.append(item_id)
    
    # Test 3: Get all news items
    print("\n📰 Testing news retrieval...")
    success, all_news = tester.test_get_all_news()
    
    # Test 4: Filter by different tags
    print("\n🏷️ Testing tag filtering...")
    filter_tags = ['Iran', 'War', 'Nuclear', 'Diplomacy']
    
    for tag in filter_tags:
        tester.test_filter_by_tag(tag)
    
    # Test 5: Case-insensitive filtering
    print("\n🔤 Testing case-insensitive filtering...")
    tester.test_case_insensitive_filter()
    
    # Test 6: Filter with 'all' tag (should return all items)
    print("\n📋 Testing 'all' filter...")
    tester.test_filter_by_tag('all')
    
    # Test 7: Non-existent tag filter
    print("\n❓ Testing non-existent tag filter...")
    tester.test_filter_by_tag('nonexistent')
    
    # Cleanup
    tester.cleanup_created_items()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())