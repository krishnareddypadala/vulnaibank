"""Chat route - LLM01: Prompt Injection & LLM07: System Prompt Leakage.

DELIBERATE VULNERABILITIES:
- No input filtering or sanitization (LLM01)
- System prompt contains secrets and is easily extractable (LLM07)
- User input directly concatenated into prompts (LLM01)
- Indirect injection via RAG context (LLM01)
- Chat history includes system messages (LLM07)
- No prompt guarding techniques (LLM07)
"""

import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, ChatMessage, Feedback
from app.ai.client import AIClient
from app.ai.prompts import get_system_prompt
from app.ai.tools import TOOL_DEFINITIONS, OLLAMA_TOOLS, execute_tool
from app.ai.rag import get_rag_context

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat')
@login_required
def index():
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(
        ChatMessage.timestamp.asc()
    ).all()
    return render_template('chat.html', messages=messages)


@chat_bp.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    """Process a chat message.

    DELIBERATE VULNERABILITY (LLM01): User input passed directly to LLM
    with no filtering, sanitization, or injection detection.
    """
    data = request.get_json()
    user_message = data.get('message', '')

    # DELIBERATE VULNERABILITY (LLM10): No input length validation
    # Save user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()

    try:
        ai_client = AIClient()

        # DELIBERATE VULNERABILITY (LLM08): RAG context from shared, uncontrolled knowledge base
        rag_context = get_rag_context(user_message, ai_client)

        # DELIBERATE VULNERABILITY (LLM04): Feedback injected into prompt
        feedback_context = get_feedback_context()

        # DELIBERATE VULNERABILITY (LLM07): System prompt with secrets
        system_prompt = get_system_prompt(
            user=current_user,
            rag_context=rag_context,
            feedback_context=feedback_context
        )

        # Build message history
        history = ChatMessage.query.filter_by(user_id=current_user.id).order_by(
            ChatMessage.timestamp.asc()
        ).limit(50).all()

        messages = [{'role': 'system', 'content': system_prompt}]
        for msg in history:
            messages.append({'role': msg.role, 'content': msg.content})

        # Get AI response with tools
        provider = ai_client.provider
        tools = TOOL_DEFINITIONS if provider == 'openai' else OLLAMA_TOOLS

        response = ai_client.chat(messages, tools=tools)

        # Process tool calls (DELIBERATE VULNERABILITY LLM06: no confirmation loop)
        max_iterations = 10  # DELIBERATE VULNERABILITY (LLM10): allows recursive tool calls
        iteration = 0
        while response.get('tool_calls') and iteration < max_iterations:
            iteration += 1
            tool_results = []
            for tc in response['tool_calls']:
                func_name = tc['function']['name']
                func_args = tc['function']['arguments']
                if isinstance(func_args, str):
                    func_args = json.loads(func_args)

                result = execute_tool(func_name, func_args)
                tool_results.append({
                    'role': 'tool',
                    'tool_call_id': tc.get('id', func_name),
                    'content': result
                })

            messages.append(response)
            messages.extend(tool_results)
            response = ai_client.chat(messages, tools=tools)

        assistant_content = response.get('content', 'I apologize, I could not process your request.')

        # Save assistant response
        assistant_msg = ChatMessage(
            user_id=current_user.id,
            role='assistant',
            content=assistant_content
        )
        db.session.add(assistant_msg)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': assistant_content
        })

    except Exception as e:
        error_msg = f'Error: {str(e)}'
        assistant_msg = ChatMessage(
            user_id=current_user.id,
            role='assistant',
            content=error_msg
        )
        db.session.add(assistant_msg)
        db.session.commit()
        return jsonify({'status': 'error', 'message': error_msg})


@chat_bp.route('/chat/history')
@login_required
def get_history():
    """DELIBERATE VULNERABILITY (LLM07): Returns all messages including system messages."""
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(
        ChatMessage.timestamp.asc()
    ).all()
    return jsonify({
        'messages': [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages
        ]
    })


@chat_bp.route('/chat/clear', methods=['POST'])
@login_required
def clear_history():
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'status': 'success'})


def get_feedback_context():
    """Get high-rated feedback to include in prompt context.

    DELIBERATE VULNERABILITY (LLM04): User-submitted feedback is
    injected directly into the system prompt without validation.
    """
    high_rated = Feedback.query.filter(Feedback.rating >= 4).order_by(
        Feedback.created_at.desc()
    ).limit(5).all()

    if not high_rated:
        return ''

    context_parts = []
    for fb in high_rated:
        context_parts.append(
            f"Previous highly-rated interaction:\n"
            f"Q: {fb.query}\nA: {fb.response}\n"
            f"User feedback: {fb.comment}"
        )
    return '\n\n'.join(context_parts)
