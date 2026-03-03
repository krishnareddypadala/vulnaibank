import json
import requests
from flask import current_app


class AIClient:
    """Unified AI client supporting both Ollama and OpenAI.

    DELIBERATE VULNERABILITY: No input validation, no output filtering,
    no token limits, no rate limiting, no timeout controls.
    """

    def __init__(self):
        self.provider = current_app.config.get('AI_PROVIDER', 'ollama')

        if self.provider == 'openai':
            import openai
            self.openai_client = openai.OpenAI(
                api_key=current_app.config.get('OPENAI_API_KEY')
            )
            self.model = current_app.config.get('OPENAI_MODEL', 'gpt-4')
        else:
            self.base_url = current_app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.model = current_app.config.get('OLLAMA_MODEL', 'llama3')

    def chat(self, messages, tools=None, temperature=0.7):
        """Send chat completion request.

        DELIBERATE VULNERABILITY (LLM10): No max_tokens limit, no timeout,
        no input length validation.
        """
        if self.provider == 'openai':
            return self._chat_openai(messages, tools, temperature)
        else:
            return self._chat_ollama(messages, tools, temperature)

    def _chat_openai(self, messages, tools=None, temperature=0.7):
        """OpenAI chat completion."""
        kwargs = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            # DELIBERATE VULNERABILITY: No max_tokens limit
        }

        if tools:
            kwargs['tools'] = tools
            kwargs['tool_choice'] = 'auto'

        try:
            response = self.openai_client.chat.completions.create(**kwargs)
            message = response.choices[0].message

            result = {
                'role': 'assistant',
                'content': message.content or '',
                'tool_calls': []
            }

            if message.tool_calls:
                for tc in message.tool_calls:
                    result['tool_calls'].append({
                        'id': tc.id,
                        'function': {
                            'name': tc.function.name,
                            'arguments': json.loads(tc.function.arguments)
                        }
                    })

            return result

        except Exception as e:
            return {
                'role': 'assistant',
                'content': f'AI Error: {str(e)}',
                'tool_calls': []
            }

    def _chat_ollama(self, messages, tools=None, temperature=0.7):
        """Ollama chat completion."""
        payload = {
            'model': self.model,
            'messages': messages,
            'stream': False,
            'options': {
                'temperature': temperature,
                # DELIBERATE VULNERABILITY: No num_predict limit
            }
        }

        if tools:
            payload['tools'] = tools

        try:
            # DELIBERATE VULNERABILITY: No timeout on request
            response = requests.post(
                f'{self.base_url}/api/chat',
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            message = data.get('message', {})
            result = {
                'role': 'assistant',
                'content': message.get('content', ''),
                'tool_calls': []
            }

            if message.get('tool_calls'):
                for tc in message['tool_calls']:
                    result['tool_calls'].append({
                        'id': f"call_{tc['function']['name']}",
                        'function': {
                            'name': tc['function']['name'],
                            'arguments': tc['function'].get('arguments', {})
                        }
                    })

            return result

        except Exception as e:
            return {
                'role': 'assistant',
                'content': f'AI Error: {str(e)}',
                'tool_calls': []
            }

    def embed(self, text):
        """Generate text embeddings for RAG.

        Uses Ollama embeddings API or OpenAI embeddings.
        Falls back to simple bag-of-words if unavailable.
        """
        if self.provider == 'openai':
            try:
                response = self.openai_client.embeddings.create(
                    model='text-embedding-3-small',
                    input=text
                )
                return response.data[0].embedding
            except Exception:
                return self._simple_embed(text)
        else:
            try:
                response = requests.post(
                    f'{self.base_url}/api/embeddings',
                    json={'model': self.model, 'prompt': text}
                )
                response.raise_for_status()
                return response.json().get('embedding', self._simple_embed(text))
            except Exception:
                return self._simple_embed(text)

    def _simple_embed(self, text):
        """Fallback: simple bag-of-words embedding (not production quality)."""
        import hashlib
        import numpy as np
        words = text.lower().split()
        vec = np.zeros(128)
        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % 128
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
