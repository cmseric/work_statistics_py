from flask import Flask, request, jsonify, Response
from services.version_service import VersionService
from services.deepseek_service import DeepSeekService
from services.ai_chat_service import AIChatService
from services.routes import register_routes
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///versions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化服务
version_service = VersionService(app)
deepseek_service = DeepSeekService(app)
ai_chat_service = AIChatService(app)

# 创建数据库表
version_service.create_tables()

# 注册路由
register_routes(
    app, 
    version_service, 
    deepseek_service,
    ai_chat_service
)

# 添加聊天路由
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({'success': False, 'error': '消息不能为空'})
    
    response = ai_chat_service.chat(messages)
    
    if response.get('success', False):
        if 'stream' in response:
            def generate():
                try:
                    for line in response['stream'].iter_lines():
                        if line:
                            try:
                                line = line.decode('utf-8')
                                if line.startswith('data: '):
                                    data = line[6:]  # Remove 'data: ' prefix
                                    if data == '[DONE]':
                                        yield 'data: [DONE]\n\n'
                                    else:
                                        try:
                                            json_data = json.loads(data)
                                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                                content = json_data['choices'][0].get('delta', {}).get('content', '')
                                                if content:
                                                    yield f'data: {json.dumps({"content": content})}\n\n'
                                        except json.JSONDecodeError as e:
                                            print(f"JSON decode error: {e}, data: {data}")
                                            continue
                            except UnicodeDecodeError as e:
                                print(f"Unicode decode error: {e}, line: {line}")
                                continue
                except Exception as e:
                    print(f"Stream error: {e}")
                    yield f'data: {json.dumps({"error": str(e)})}\n\n'
                finally:
                    yield 'data: [DONE]\n\n'
            
            return Response(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no'
                }
            )
        else:
            return jsonify(response)
    else:
        return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True) 