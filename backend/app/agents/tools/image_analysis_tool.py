"""Image Analysis Tool for App Testing"""

import base64
from typing import Optional
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ImageAnalysisTool:
    """Tool for analyzing screenshots using AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if self.api_key:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=self.api_key
            )
        else:
            self.llm = None
            logger.warning("No OpenAI API key provided for image analysis")
    
    def analyze_screenshot(self, image_path: str, prompt: Optional[str] = None) -> str:
        """Analyze a screenshot and return description"""
        if not self.llm:
            return "Image analysis not available - OpenAI API key required"
            
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Default prompt if none provided
            if not prompt:
                prompt = """Analyze this mobile app screenshot and describe:
                1. What screen/feature is shown
                2. Key UI elements visible
                3. Any potential issues or improvements
                4. Accessibility considerations
                Keep the response concise and focused on testing insights."""
            
            # Create message with image
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            )
            
            # Get analysis
            response = self.llm.invoke([message])
            return response.content
            
        except Exception as e:
            logger.error(f"Error analyzing screenshot: {str(e)}")
            return f"Error analyzing image: {str(e)}"
    
    def create_tool(self) -> Tool:
        """Create the image analysis tool for CrewAI"""
        return Tool(
            name="analyze_screenshot",
            func=lambda params: self.analyze_screenshot(
                params.split('|')[0],
                params.split('|')[1] if '|' in params else None
            ),
            description="Analyze a screenshot using AI. Input: 'image_path|optional_prompt'"
        )