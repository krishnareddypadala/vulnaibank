"""Documents route - LLM03: Supply Chain & LLM08: Vector/Embedding Weaknesses.

DELIBERATE VULNERABILITIES:
- LLM03: Plugin loading via exec(), pickle deserialization
- LLM08: No access controls on RAG knowledge base
- LLM08: Any user can poison shared document store
- LLM03: No code integrity verification
"""

import pickle
import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Document, Plugin
from app.ai.rag import add_document

documents_bp = Blueprint('documents', __name__)


@documents_bp.route('/documents')
@login_required
def index():
    # DELIBERATE VULNERABILITY (LLM08): Shows ALL documents, not just user's
    documents = Document.query.order_by(Document.created_at.desc()).all()
    plugins = Plugin.query.all() if current_user.role == 'admin' else []
    return render_template('documents.html', documents=documents, plugins=plugins)


@documents_bp.route('/documents/upload', methods=['POST'])
@login_required
def upload_document():
    """Upload a document to the shared knowledge base.

    DELIBERATE VULNERABILITY (LLM08): No content validation,
    uploaded content affects ALL users' AI interactions.
    Can be used for indirect prompt injection (LLM01).
    """
    if request.is_json:
        data = request.get_json()
        filename = data.get('filename', 'untitled.txt')
        content = data.get('content', '')
    else:
        file = request.files.get('file')
        if file:
            filename = file.filename
            content = file.read().decode('utf-8', errors='ignore')
        else:
            return jsonify({'error': 'No file provided'}), 400

    # DELIBERATE VULNERABILITY: No content sanitization
    doc = add_document(
        filename=filename,
        content=content,
        user_id=current_user.id,
        doc_type='user_upload'
    )

    return jsonify({
        'status': 'success',
        'message': f'Document "{filename}" uploaded to knowledge base',
        'doc_id': doc.id
    })


@documents_bp.route('/documents/<int:doc_id>')
@login_required
def view_document(doc_id):
    """DELIBERATE VULNERABILITY (LLM08): No access control on document viewing."""
    doc = Document.query.get_or_404(doc_id)
    return jsonify({
        'id': doc.id,
        'filename': doc.filename,
        'content': doc.content,
        'type': doc.doc_type,
        'uploaded_by': doc.user.username if doc.user else 'system'
    })


@documents_bp.route('/documents/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    db.session.delete(doc)
    db.session.commit()
    return jsonify({'status': 'success'})


# ---- LLM03: Supply Chain Vulnerabilities ----

@documents_bp.route('/documents/import-model', methods=['POST'])
@login_required
def import_model():
    """Import a serialized model/data file.

    DELIBERATE VULNERABILITY (LLM03): Unsafe pickle deserialization.
    Attacker can craft a pickle payload for arbitrary code execution.
    """
    file = request.files.get('model_file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    try:
        # DELIBERATE VULNERABILITY: Unsafe deserialization
        data = pickle.loads(file.read())
        return jsonify({
            'status': 'success',
            'message': 'Model imported successfully',
            'data_type': str(type(data).__name__),
            'data_preview': str(data)[:500]
        })
    except Exception as e:
        return jsonify({'error': f'Import failed: {str(e)}'}), 400


@documents_bp.route('/documents/install-plugin', methods=['POST'])
@login_required
def install_plugin():
    """Install a custom plugin.

    DELIBERATE VULNERABILITY (LLM03): Executes arbitrary Python code via exec().
    No sandboxing, no code review, no integrity checks.
    """
    data = request.get_json()
    name = data.get('name', 'Unnamed Plugin')
    description = data.get('description', '')
    code = data.get('code', '')

    # DELIBERATE VULNERABILITY: Store and execute arbitrary code
    plugin = Plugin(
        name=name,
        description=description,
        code=code,
        enabled=True
    )
    db.session.add(plugin)
    db.session.commit()

    # DELIBERATE VULNERABILITY: Execute plugin code immediately
    try:
        exec(code)
        return jsonify({
            'status': 'success',
            'message': f'Plugin "{name}" installed and activated',
            'plugin_id': plugin.id
        })
    except Exception as e:
        return jsonify({
            'status': 'warning',
            'message': f'Plugin installed but execution failed: {str(e)}',
            'plugin_id': plugin.id
        })


@documents_bp.route('/documents/run-plugin/<int:plugin_id>', methods=['POST'])
@login_required
def run_plugin(plugin_id):
    """Run an installed plugin.

    DELIBERATE VULNERABILITY (LLM03): Executes stored code via exec().
    """
    plugin = Plugin.query.get_or_404(plugin_id)

    try:
        # DELIBERATE VULNERABILITY: exec() on stored code
        local_vars = {}
        exec(plugin.code, {}, local_vars)
        return jsonify({
            'status': 'success',
            'message': f'Plugin "{plugin.name}" executed',
            'output': str(local_vars)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
