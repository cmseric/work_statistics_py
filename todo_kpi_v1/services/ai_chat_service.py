from flask import Flask
import requests
import os
from typing import Dict, Any, Optional
from services.deepseek_service import DeepSeekService

class AIChatService:
    def __init__(self, app: Flask):
        self.app = app
        self.deepseek_service = DeepSeekService(app)
        self._setup_config()

    def _setup_config(self):
        self.model = os.getenv('SILICONFLOW_MODEL', 'Pro/deepseek-ai/DeepSeek-V3')
        self.max_tokens = int(os.getenv('SILICONFLOW_MAX_TOKENS', '512'))
        self.temperature = float(os.getenv('SILICONFLOW_TEMPERATURE', '0.7'))
        self.top_p = float(os.getenv('SILICONFLOW_TOP_P', '0.7'))
        self.top_k = int(os.getenv('SILICONFLOW_TOP_K', '50'))
        self.frequency_penalty = float(os.getenv('SILICONFLOW_FREQUENCY_PENALTY', '0.5'))

    def chat(self, messages: list) -> Dict[str, Any]:
        """Send a chat message and get response"""
        try:
            response = self.deepseek_service.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                frequency_penalty=self.frequency_penalty,
                stream=True,
                n=1,
                response_format={"type": "text"},
                tools=[]
            )
            
            if response.get('success', False):
                if 'stream' in response:
                    # Return the stream object for SSE handling
                    return {
                        'success': True,
                        'stream': response['stream']
                    }
                else:
                    return {
                        'success': True,
                        'response': response['response']['choices'][0]['message']['content']
                    }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Unknown error')
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 