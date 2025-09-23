# backend/routes/llm_routes.py
import traceback
from flask import Blueprint, request, render_template, jsonify
from flask_login import login_required, current_user
from ..services import llm_service

llm_routes = Blueprint('llm', __name__, url_prefix='/llm')

@llm_routes.route('/chat')
@login_required
def chat_page():
    """Renders the main chat interface page."""
    return render_template('llm_chat.html', title="LLM Chat")

@llm_routes.route('/api/chat', methods=['POST'])
@login_required
def handle_chat():
    """API endpoint to handle a chat message from the user."""
    data = request.json
    user_message = data.get('message')
    model_name = data.get('model')
    system_prompt = current_user.system_prompt

    if not user_message or not model_name:
        return jsonify({"success": False, "message": "Message and model are required."}), 400

    try:
        chat_history = llm_service.get_chat_history()
        response = llm_service.generate_chat_response(
            model_name=model_name,
            user_message=user_message,
            system_prompt=system_prompt,
            chat_history=chat_history
        )
        if response.get("success"):
            llm_service.add_message_to_history('user', user_message)
            llm_service.add_message_to_history('assistant', response["message"])
        return jsonify(response)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": f"An unexpected error occurred: {e}"}), 500

@llm_routes.route('/api/get_models', methods=['GET'])
@login_required
def get_llm_models():
    """API endpoint to fetch available LLM models."""
    models = llm_service.get_all_available_llm_models()
    return jsonify({"success": True, "models": models})

@llm_routes.route('/api/get_history', methods=['GET'])
@login_required
def get_chat_history():
    """API endpoint to fetch the current chat session's history."""
    history = llm_service.get_chat_history()
    return jsonify({"success": True, "history": history})

@llm_routes.route('/api/clear_history', methods=['POST'])
@login_required
def clear_chat_history():
    """API endpoint to clear the chat history from the session."""
    llm_service.clear_chat_history()
    return jsonify({"success": True, "message": "Chat history cleared."})

@llm_routes.route('/api/system_prompt', methods=['POST'])
@login_required
def save_system_prompt():
    """API endpoint to save the user's system prompt."""
    prompt = request.json.get('prompt')
    success, message = llm_service.save_user_system_prompt(current_user.id, prompt)
    if not success:
        return jsonify({"success": False, "message": message}), 404
    return jsonify({"success": True, "message": message})