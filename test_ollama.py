"""
Test script for Ollama integration.
"""

from ai_service import AIService

def test_ollama():
    """Test Ollama connection and basic operations."""
    
    print("=" * 60)
    print("Testing Ollama Integration")
    print("=" * 60)
    
    # Initialize AI service
    ai_service = AIService(model="llama2", host="http://localhost:11434")
    
    # Test 1: Check if service is available
    print("\n1. Checking if Ollama service is available...")
    if ai_service.is_available():
        print("✅ Ollama service is ONLINE")
    else:
        print("❌ Ollama service is OFFLINE")
        print("Please make sure Ollama is running with: ollama serve")
        return
    
    # Test 2: List available models
    print("\n2. Listing available models...")
    models = ai_service.list_models()
    if models:
        print(f"✅ Available models: {', '.join(models)}")
    else:
        print("⚠️ No models found")
    
    # Test 3: Simple chat
    print("\n3. Testing simple chat...")
    try:
        response = ai_service.chat("Hello! Can you introduce yourself in one sentence?")
        print(f"✅ Chat response: {response}")
    except Exception as e:
        print(f"❌ Chat error: {e}")
    
    # Test 4: Summarize text
    print("\n4. Testing summarization...")
    test_text = """
    Uber exits Nigeria after 12 years, saying the market is too competitive. 
    The ride-hailing company has been struggling to compete with local rivals 
    like Bolt and inDrive. This exit marks a significant shift in the Nigerian 
    transportation landscape.
    """
    try:
        summary = ai_service.summarize(test_text, max_length=100)
        print(f"✅ Summary: {summary}")
    except Exception as e:
        print(f"❌ Summarize error: {e}")
    
    # Test 5: Analyze articles
    print("\n5. Testing article analysis...")
    test_articles = [
        {
            'title': 'Uber exits Nigeria',
            'content': 'Uber leaves Nigeria after 12 years due to competition.'
        },
        {
            'title': 'OPay denies shutdown',
            'content': 'OPay denies rumors of shutting down operations.'
        }
    ]
    try:
        analysis = ai_service.analyze_articles(test_articles)
        print(f"✅ Analysis: {analysis[:200]}...")
    except Exception as e:
        print(f"❌ Analyze error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Ollama integration test completed")
    print("=" * 60)

if __name__ == "__main__":
    test_ollama()
