"""Feedback route - LLM04: Data and Model Poisoning.

DELIBERATE VULNERABILITIES:
- User feedback directly injected into AI system prompt
- No validation on feedback content
- High-rated feedback automatically influences AI behavior
- Training data endpoint accepts arbitrary JSON
- Can inject malicious instructions via feedback comments
"""

import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Feedback

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/feedback')
@login_required
def index():
    feedbacks = Feedback.query.filter_by(user_id=current_user.id).order_by(
        Feedback.created_at.desc()
    ).all()
    all_feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(50).all()
    return render_template('feedback.html',
                           my_feedbacks=feedbacks,
                           all_feedbacks=all_feedbacks)


@feedback_bp.route('/feedback/submit', methods=['POST'])
@login_required
def submit_feedback():
    """Submit feedback on an AI interaction.

    DELIBERATE VULNERABILITY (LLM04): Feedback content is stored and
    later injected into AI system prompts without any validation.
    An attacker can submit carefully crafted feedback with malicious
    instructions that will influence all future AI interactions.
    """
    data = request.get_json()

    feedback = Feedback(
        user_id=current_user.id,
        query=data.get('query', ''),
        response=data.get('response', ''),
        rating=int(data.get('rating', 3)),
        # DELIBERATE VULNERABILITY: No content validation on comment
        comment=data.get('comment', '')
    )
    db.session.add(feedback)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Feedback submitted. High-rated feedback will influence AI responses.',
        'feedback_id': feedback.id
    })


@feedback_bp.route('/feedback/training-data', methods=['POST'])
@login_required
def submit_training_data():
    """Submit training data to fine-tune AI behavior.

    DELIBERATE VULNERABILITY (LLM04): Accepts arbitrary training data
    with no validation, review, or approval process.
    """
    data = request.get_json()
    examples = data.get('examples', [])

    # DELIBERATE VULNERABILITY: Store unvalidated training examples as feedback
    for example in examples:
        feedback = Feedback(
            user_id=current_user.id,
            query=example.get('input', ''),
            response=example.get('output', ''),
            rating=5,  # Auto high-rate to ensure injection into prompt
            comment=example.get('context', 'Training data submission')
        )
        db.session.add(feedback)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'{len(examples)} training examples submitted',
        'note': 'These will be included in future AI interactions'
    })


@feedback_bp.route('/feedback/export')
@login_required
def export_feedback():
    """Export all feedback data.

    DELIBERATE VULNERABILITY: Exposes all users' feedback without access control.
    """
    feedbacks = Feedback.query.all()
    return jsonify({
        'feedbacks': [
            {
                'id': f.id,
                'user_id': f.user_id,
                'username': f.user.username,
                'query': f.query,
                'response': f.response,
                'rating': f.rating,
                'comment': f.comment,
                'created_at': f.created_at.isoformat()
            } for f in feedbacks
        ]
    })
