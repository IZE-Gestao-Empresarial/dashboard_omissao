from __future__ import annotations

from typing import Any, Dict

import requests
import streamlit as st


DEFAULT_TIMEOUT = 25
CACHE_TTL_SECONDS = 240


def _safe_json(resp: requests.Response) -> Dict[str, Any]:
    try:
        data = resp.json()
        return data if isinstance(data, dict) else {"ok": False, "message": "Resposta JSON inválida.", "data": data}
    except Exception:
        return {
            "ok": False,
            "message": "Resposta não-JSON do endpoint.",
            "status_code": resp.status_code,
            "text": resp.text[:1000],
        }


def _fetch(url: str, token: str, sheet: str, area: str | None = None) -> Dict[str, Any]:
    params = {"token": token, "sheet": sheet}
    if area:
        params["area"] = area
    response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return _safe_json(response)


def fetch_dashboard_payload(url: str, token: str, sheet: str, area: str | None = None) -> Dict[str, Any]:
    try:
        payload = _fetch(url=url, token=token, sheet=sheet, area=area)
    except requests.HTTPError as exc:
        response = exc.response
        details = _safe_json(response) if response is not None else {}
        return {
            "ok": False,
            "message": f"Erro HTTP ao consultar a API: {exc}",
            "details": details,
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "message": f"Erro de conexão ao consultar a API: {exc}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "message": f"Erro inesperado ao carregar o dashboard: {exc}",
        }

    if "cards" not in payload:
        return {
            "ok": False,
            "message": "O JSON retornado não possui a chave 'cards'.",
            "payload": payload,
        }

    payload.setdefault("ok", True)
    return payload