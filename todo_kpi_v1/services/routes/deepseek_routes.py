from flask import Flask, request, jsonify
from ..deepseek_service import DeepSeekService

def register_deepseek_routes(app: Flask, deepseek_service: DeepSeekService):
    """注册DeepSeek相关路由"""
    @app.route('/api/deepseek/chat', methods=['POST'])
    def deepseek_chat():
        data = request.get_json()
        messages = data.get('messages', [])
        model = data.get('model', 'Pro/deepseek-ai/DeepSeek-V3')
        max_tokens = data.get('max_tokens', 512)
        temperature = data.get('temperature', 0.7)
        
        response = deepseek_service.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return jsonify(response)

    @app.route('/api/deepseek/embedding', methods=['POST'])
    def embedding():
        data = request.get_json()
        text = data.get('text', '')
        model = data.get('model', 'deepseek-embedding')
        
        response = deepseek_service.text_embedding(text, model)
        return jsonify(response)

    @app.route('/api/deepseek/generation', methods=['POST'])
    def generation():
        data = request.get_json()
        prompt = data.get('prompt', '')
        model = data.get('model', 'deepseek-coder')
        
        response = deepseek_service.text_generation(prompt, model)
        return jsonify(response) 