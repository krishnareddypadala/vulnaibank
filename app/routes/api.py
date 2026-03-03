"""API route - LLM10: Unbounded Consumption.

DELIBERATE VULNERABILITIES:
- No rate limiting on any endpoint
- No input length validation
- No max_tokens limit on AI responses
- No timeout controls
- No authentication on some endpoints
- Debug endpoint exposes system prompt (LLM07)
"""

import json
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, ChatMessage
from app.ai.client import AIClient
from app.ai.prompts import get_system_prompt, BANKING_SYSTEM_PROMPT
from app.ai.tools import TOOL_DEFINITIONS, OLLAMA_TOOLS, execute_tool
from config import Config

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/chat', methods=['POST'])
def api_chat():
    """Public chat API endpoint.

    DELIBERATE VULNERABILITY (LLM10): No rate limiting, no input length limit,
    no authentication required, no token budget.
    """
    data = request.get_json()
    message = data.get('message', '')
    # DELIBERATE VULNERABILITY: No input length check - can send megabytes

    try:
        ai_client = AIClient()
        system_prompt = get_system_prompt()

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': message}
        ]

        provider = ai_client.provider
        tools = TOOL_DEFINITIONS if provider == 'openai' else OLLAMA_TOOLS

        # DELIBERATE VULNERABILITY (LLM10): No timeout, recursive tool calling
        response = ai_client.chat(messages, tools=tools)

        max_iterations = 100  # DELIBERATE VULNERABILITY: Very high iteration limit
        iteration = 0
        while response.get('tool_calls') and iteration < max_iterations:
            iteration += 1
            for tc in response['tool_calls']:
                func_name = tc['function']['name']
                func_args = tc['function']['arguments']
                if isinstance(func_args, str):
                    func_args = json.loads(func_args)

                result = execute_tool(func_name, func_args)
                messages.append(response)
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tc.get('id', func_name),
                    'content': result
                })

            response = ai_client.chat(messages, tools=tools)

        return jsonify({
            'response': response.get('content', ''),
            'iterations': iteration
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/batch', methods=['POST'])
def api_batch():
    """Batch processing endpoint.

    DELIBERATE VULNERABILITY (LLM10): Process unlimited batch requests
    with no limits on count or size.
    """
    data = request.get_json()
    queries = data.get('queries', [])
    # DELIBERATE VULNERABILITY: No limit on batch size

    results = []
    ai_client = AIClient()

    for query in queries:
        messages = [
            {'role': 'system', 'content': get_system_prompt()},
            {'role': 'user', 'content': query}
        ]
        response = ai_client.chat(messages)
        results.append(response.get('content', ''))

    return jsonify({'results': results, 'count': len(results)})


@api_bp.route('/debug')
def api_debug():
    """Debug endpoint.

    DELIBERATE VULNERABILITY (LLM07): Exposes system prompt, configuration,
    and internal details. No authentication required.
    """
    return jsonify({
        'system_prompt': BANKING_SYSTEM_PROMPT,
        'config': {
            'ai_provider': Config.AI_PROVIDER,
            'ollama_base_url': Config.OLLAMA_BASE_URL,
            'ollama_model': Config.OLLAMA_MODEL,
            'openai_model': Config.OPENAI_MODEL,
            'openai_api_key': Config.OPENAI_API_KEY,
            'database_uri': Config.SQLALCHEMY_DATABASE_URI,
            'internal_api': Config.INTERNAL_API_ENDPOINT,
            'admin_api_key': Config.ADMIN_API_KEY,
            'secret_key': Config.SECRET_KEY
        },
        'tools': [t['function']['name'] for t in TOOL_DEFINITIONS]
    })


@api_bp.route('/health')
def api_health():
    return jsonify({'status': 'ok', 'service': 'vulnaibank'})


@api_bp.route('/tools/execute', methods=['POST'])
def api_execute_tool():
    """Direct tool execution endpoint.

    DELIBERATE VULNERABILITY (LLM06/LLM10): Execute any tool directly
    without authentication or authorization.
    """
    data = request.get_json()
    tool_name = data.get('tool', '')
    arguments = data.get('arguments', {})

    result = execute_tool(tool_name, arguments)
    return jsonify({'result': json.loads(result) if isinstance(result, str) else result})
