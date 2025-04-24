from flask import Flask
from dotenv import load_dotenv
import requests
import os
import json
from typing import Dict, Any, Optional, List

load_dotenv()

class DeepSeekService:
    def __init__(self, app: Flask):
        self.app = app
        self._setup_config()

    def _setup_config(self):
        # 设置SiliconFlow API配置
        self.api_key = os.getenv('SILICONFLOW_API_KEY')
        self.api_base = os.getenv('SILICONFLOW_API_BASE', 'https://api.siliconflow.com/v1')
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY environment variable is not set")

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            "Accept": "application/json",
            'Content-Type': 'application/json'
        }

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "Pro/deepseek-ai/DeepSeek-V3",
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.7,
        top_k: int = 50,
        frequency_penalty: float = 0.5,
        stream: bool = False,
        n: int = 1,
        response_format: Dict[str, str] = None,
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a chat completion request to SiliconFlow API"""
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self._get_headers(),
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "frequency_penalty": frequency_penalty,
                    "n": n,
                    "response_format": response_format or {"type": "text"},
                    "tools": tools or []
                },
                stream=stream  # Enable streaming for requests
            )
            
            if response.status_code == 200:
                if stream:
                    full_content = ""
                    full_reasoning_content = ""

                    for chunk in response.iter_lines():
                        if chunk:
                            chunk_str = chunk.decode('utf-8').replace('data: ', '')
                            if chunk_str != "[DONE]":
                                chunk_data = json.loads(chunk_str)
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                reasoning_content = delta.get('reasoning_content', '')
                                if content:
                                    print(content, end="", flush=True)
                                    full_content += content
                                if reasoning_content:
                                    print(reasoning_content, end="", flush=True)
                                    full_reasoning_content += reasoning_content
                else:
                    return {
                        'success': True,
                        'response': response.json()
                    }
            else:
                return {
                    'success': False,
                    'error': f"API request failed with status {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def text_embedding(self, text: str, model: str = "deepseek-embedding") -> Dict[str, Any]:
        """
        使用DeepSeek模型生成文本嵌入
        """
        try:
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers=self._get_headers(),
                json={
                    "model": model,
                    "input": text
                }
            )
            response.raise_for_status()
            return {
                "success": True,
                "embedding": response.json()["data"][0]["embedding"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def text_generation(self, prompt: str, model: str = "deepseek-coder") -> Dict[str, Any]:
        """
        使用DeepSeek模型生成文本
        """
        try:
            response = requests.post(
                f"{self.api_base}/completions",
                headers=self._get_headers(),
                json={
                    "model": model,
                    "prompt": prompt,
                }
            )
            response.raise_for_status()
            return {
                "success": True,
                "text": response.json()["choices"][0]["text"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 