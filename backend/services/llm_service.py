# backend/services/llm_service.py
import requests
import os
import time
import traceback
from flask import session as flask_session, current_app
from collections import deque
import logging
from flask_login import current_user
from ..db import db
from ..models import User, LLMSettings
from sqlalchemy.orm import joinedload

# --- SDK Imports ---
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Global Apollo Token Cache ---
_apollo_access_token = None
_apollo_token_expiry = 0

# --- API Key & URL Retrieval Functions ---

def get_apollo_client_credentials():
    if current_user.is_authenticated and current_user.llm_settings:
        if current_user.llm_settings.apollo_client_id and current_user.llm_settings.apollo_client_secret:
            return current_user.llm_settings.apollo_client_id, current_user.llm_settings.apollo_client_secret
    return current_app.config.get('APOLLO_CLIENT_ID'), current_app.config.get('APOLLO_CLIENT_SECRET')

def get_anthropic_api_key():
    """Retrieve Anthropic API key from user settings or fallback to config."""
    if current_user.is_authenticated and current_user.llm_settings:
        if current_user.llm_settings.anthropic_api_key:
            return current_user.llm_settings.anthropic_api_key
    return current_app.config.get('ANTHROPIC_API_KEY')

def get_apollo_access_token():
    global _apollo_access_token, _apollo_token_expiry
    if _apollo_access_token and time.time() < _apollo_token_expiry:
        return _apollo_access_token
    
    client_id, client_secret = get_apollo_client_credentials()
    token_url = current_app.config.get('APOLLO_TOKEN_URL')
    
    if not all([client_id, client_secret, token_url]):
        raise ValueError("Apollo credentials or TOKEN_URL not configured.")

    try:
        response = requests.post(
            token_url,
            data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
            timeout=10
        )
        response.raise_for_status()
        json_response = response.json()
        _apollo_access_token = json_response['access_token']
        _apollo_token_expiry = time.time() + json_response.get('expires_in', 3500)
        return _apollo_access_token
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Apollo Token Error: Network request failed: {e}") from e

# --- Chat History Management ---

def _get_history_deque():
    max_len = current_app.config.get('MAX_CHAT_HISTORY_LENGTH', 20)
    return deque(flask_session.get('llm_chat_history', []), maxlen=max_len)

def _save_history_deque(history_deque):
    flask_session['llm_chat_history'] = list(history_deque)
    flask_session.modified = True

def get_chat_history():
    return list(_get_history_deque())

def add_message_to_history(role, content):
    history_deque = _get_history_deque()
    history_deque.append({'role': role, 'content': content})
    _save_history_deque(history_deque)

def clear_chat_history():
    flask_session.pop('llm_chat_history', None)

# --- Provider-Specific API Call ---

def _call_apollo(model_id, messages, **kwargs):
    llm_model = ChatOpenAI(
        model=model_id,
        base_url=current_app.config.get('APOLLO_LLM_API_BASE_URL'),
        api_key=get_apollo_access_token(),
        temperature=0.1,
        timeout=300
    )
    response = llm_model.invoke(messages)
    return response.content

def _call_anthropic(model_id, messages, **kwargs):
    """Call Anthropic API using LangChain."""
    api_key = get_anthropic_api_key()
    if not api_key:
        raise ValueError("Anthropic API key not configured.")
    
    llm_model = ChatAnthropic(
        model=model_id,
        api_key=api_key,
        temperature=0.1,
        timeout=300
    )
    response = llm_model.invoke(messages)
    return response.content

# --- Main Dispatcher Function ---

PROVIDER_HANDLERS = {
    "apollo": _call_apollo,
    "anthropic": _call_anthropic
}

def generate_chat_response(model_name, user_message, system_prompt, chat_history):
    provider, model_id = model_name.split('-', 1) if '-' in model_name else ("unknown", model_name)
    handler = PROVIDER_HANDLERS.get(provider)
    if not handler:
        return {"success": False, "message": f"Unsupported LLM provider: {provider}"}

    messages_for_api = []
    if system_prompt:
        messages_for_api.append({'role': 'system', 'content': system_prompt})
    if chat_history:
        messages_for_api.extend(chat_history)
    messages_for_api.append({'role': 'user', 'content': user_message})

    try:
        logging.info(f"Calling provider '{provider}' with model '{model_id}'...")
        assistant_message = handler(model_id=model_id, messages=messages_for_api)
        return {"success": True, "message": assistant_message}
    except Exception as e:
        error_msg = f"Error from {provider.capitalize()} API: {e}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return {"success": False, "message": error_msg}

# --- Model Discovery ---

def get_available_apollo_models():
    apollo_url = current_app.config.get('APOLLO_LLM_API_BASE_URL')
    if not apollo_url: return []
    try:
        access_token = get_apollo_access_token()
        response = requests.get(f"{apollo_url}/model_group/info", headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
        response.raise_for_status()
        return [f"apollo-{model['model_group']}" for model in response.json().get('data', []) if model.get('mode') == 'chat']
    except Exception as e:
        return [f"apollo-Error: {e.__class__.__name__}"]

def get_available_anthropic_models():
    """Return Anthropic models if API key is configured."""
    api_key = get_anthropic_api_key()
    if not api_key:
        return []
    
    # Anthropic's popular models as of 2025
    return [
        "anthropic-claude-sonnet-4-20250514",
        "anthropic-claude-3-7-sonnet-20250219",
        "anthropic-claude-3-5-sonnet-20241022",
        "anthropic-claude-3-5-sonnet-20240620",
        "anthropic-claude-3-5-haiku-20241022",
        "anthropic-claude-3-opus-20240229",
        "anthropic-claude-3-haiku-20240307"
    ]

def get_all_available_llm_models():
    """Aggregate all available models from all configured providers."""
    all_models = []
    all_models.extend(get_available_apollo_models())
    all_models.extend(get_available_anthropic_models())
    return all_models

# --- User Prompt Management ---

def save_user_system_prompt(user_id, prompt_content):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."
    user.system_prompt = prompt_content
    db.session.commit()
    return True, "System prompt saved successfully."