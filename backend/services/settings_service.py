# backend/services/settings_service.py
from ..db import db
from ..models import User, LLMSettings

def get_user_llm_settings(user_id: int):
    """Retrieves the LLMSettings for a given user."""
    user = User.query.filter(User.id == user_id).one_or_none()
    return user.llm_settings if user else None

def save_user_llm_settings(user: User, form_data: dict):
    """Saves or updates LLMSettings for a given user."""
    user_settings = user.llm_settings
    if not user_settings:
        user_settings = LLMSettings(user=user)
        db.session.add(user_settings)
    
    user_settings.openai_api_key = form_data.get('openai_api_key', '').strip() or None
    user_settings.anthropic_api_key = form_data.get('anthropic_api_key', '').strip() or None
    user_settings.google_api_key = form_data.get('google_api_key', '').strip() or None
    user_settings.ollama_base_url = form_data.get('ollama_base_url', '').strip() or None
    user_settings.apollo_client_id = form_data.get('apollo_client_id', '').strip() or None
    user_settings.apollo_client_secret = form_data.get('apollo_client_secret', '').strip() or None
    
    db.session.commit()
    return True, "LLM settings updated successfully!"