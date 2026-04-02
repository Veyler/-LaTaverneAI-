"""
Couche API — abstraction autour du client OpenAI.
Supporte plusieurs providers (base_url + api_key indépendants par modèle).
"""

from openai import OpenAI
from core.config import AVAILABLE_MODELS, PROVIDERS, DEFAULT_TEMPERATURE, DEFAULT_TOP_P


def _get_model_config(model_id: str) -> dict:
    for m in AVAILABLE_MODELS:
        if m["id"] == model_id:
            return m
    return AVAILABLE_MODELS[0]


def _get_provider(provider_id: str) -> dict:
    for p in PROVIDERS:
        if p["id"] == provider_id:
            return p
    return PROVIDERS[0]


def _build_client(model_id: str) -> OpenAI:
    """Construit un client OpenAI avec la bonne base_url et api_key pour ce modèle."""
    cfg = _get_model_config(model_id)
    provider = _get_provider(cfg.get("provider_id", PROVIDERS[0]["id"]))
    return OpenAI(base_url=provider["base_url"], api_key=provider["api_key"])


def send_message(
    messages: list[dict],
    model_id: str,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    on_chunk=None,
    stream: bool = False,
    system_prompt: str = None,
) -> dict:
    client = _build_client(model_id)
    cfg = _get_model_config(model_id)
    max_tokens = cfg.get("max_tokens", 4096)

    # Prepend system prompt if provided
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages

    if stream and on_chunk:
        completion = client.chat.completions.create(
            model=model_id, messages=messages,
            temperature=temperature, top_p=top_p,
            max_tokens=max_tokens, stream=True,
        )
        full_content = ""
        for chunk in completion:
            delta = chunk.choices[0].delta
            if delta.content:
                full_content += delta.content
                on_chunk(delta.content)
        return {"content": full_content, "reasoning": None, "model_id": model_id}
    else:
        completion = client.chat.completions.create(
            model=model_id, messages=messages,
            temperature=temperature, top_p=top_p,
            max_tokens=max_tokens, stream=False,
        )
        msg = completion.choices[0].message
        reasoning = getattr(msg, "reasoning_content", None)
        return {
            "content": msg.content or "",
            "reasoning": reasoning,
            "model_id": model_id,
        }


def generate_title(first_message: str, model_id: str) -> str:
    try:
        client = _build_client(model_id)
        completion = client.chat.completions.create(
            model=model_id,
            messages=[{
                "role": "user",
                "content": (
                    f"Génère un titre très court (max 6 mots, sans guillemets, sans ponctuation finale) "
                    f"pour une conversation qui commence par : '{first_message[:200]}'"
                )
            }],
            temperature=0.5, max_tokens=30, stream=False,
        )
        title = completion.choices[0].message.content.strip().strip('"\'')
        return title[:60] if title else "Nouvelle conversation"
    except Exception:
        return first_message[:40] + ("..." if len(first_message) > 40 else "")
