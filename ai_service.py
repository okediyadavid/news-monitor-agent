"""
AI Service module for Ollama integration.
Provides AI capabilities using local Llama models via Ollama.
"""

import ollama
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with Ollama AI models."""
    
    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        """
        Initialize the AI service.
        
        Args:
            model: The Ollama model to use (default: llama3.2)
            host: The Ollama server host (default: http://localhost:11434)
        """
        self.model = model
        self.host = host
        self.client = ollama.Client(host=host)
        
    def chat(self, message: str, context: Optional[str] = None) -> str:
        """
        Send a chat message to the AI model.
        
        Args:
            message: The user's message
            context: Optional context to include in the conversation
            
        Returns:
            The AI's response
        """
        try:
            messages = []
            
            if context:
                messages.append({
                    'role': 'system',
                    'content': context
                })
            
            messages.append({
                'role': 'user',
                'content': message
            })
            
            response = self.client.chat(model=self.model, messages=messages)
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Error: {str(e)}"
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """
        Summarize the given text.
        
        Args:
            text: The text to summarize
            max_length: Maximum length of the summary
            
        Returns:
            The summary
        """
        try:
            prompt = f"Please summarize the following text in {max_length} characters or less:\n\n{text}"
            
            response = self.client.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error in summarize: {e}")
            return f"Error: {str(e)}"
    
    def analyze_articles(self, articles: List[dict]) -> str:
        """
        Analyze a list of articles and provide insights.
        
        Args:
            articles: List of article dictionaries with 'title' and 'content'
            
        Returns:
            Analysis of the articles
        """
        try:
            article_text = "\n\n".join([
                f"Title: {a.get('title', 'N/A')}\nContent: {a.get('content', 'N/A')[:500]}"
                for a in articles[:5]  # Limit to 5 articles to avoid token limits
            ])
            
            prompt = f"""Analyze the following news articles and provide:
1. Key themes and trends
2. Important insights
3. Potential implications

Articles:
{article_text}"""
            
            response = self.client.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error in analyze_articles: {e}")
            return f"Error: {str(e)}"
    
    def is_available(self) -> bool:
        """
        Check if the Ollama service is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama service not available: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models.
        
        Returns:
            List of model names
        """
        try:
            models = self.client.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
