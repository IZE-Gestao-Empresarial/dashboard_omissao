from __future__ import annotations

from csv import DictReader
from io import StringIO
from typing import Any, Dict
import unicodedata
from urllib.parse import quote, urlencode

import requests
import streamlit as st


DEFAULT_TIMEOUT = 30
CACHE_TTL_SECONDS = 240

DEFAULT_DASHBOARD_SPREADSHEET_ID = "1dBo7PKwJfpsujZl339rV-sks3jlu8AKbNROKSMZT210"

STAGE_TO_CARD = {
    "BASE": "base",
    "ATUALIZACAO": "atualizacao",
    "ATUALIZACAO": "atualizacao",
    "ROTINA": "rotina",
    "TEC": "produto",
}

CARD_TITLES = {
    "base": "Base",
    "atualizacao": "Atualizacao",
    "rotina": "Rotina",
    "produto": "Produto",
}

PERCENT_INDICATORS = {
    "FC",
    "DRE",
    "INDICADORES",
    "RADAR ENVIADOS SEMANA",
    "NAO ELEGIVEIS RADAR",
    "RELATORIOS ENVIADOS NO MES",
    "EXCECOES RELATORIOS",
    "CLIENTES INTEGRADOS",
    "DE PARA INCORRETOS",
    "ERRO ATUALIZACAO DASH HOJE",
    "ERROS ATT HOJE",
}


def _strip_accents(value: str) -> str:
    return unicodedata.normalize("NFD", value).encode("ascii", "ignore").decode("ascii")


def _normalize_key(value: str | None) -> str:
    raw = _strip_accents(str(value or "")).strip().upper()
    return " ".join(raw.replace("_", " ").replace("-", " ").split())


def _find_column(row: dict[str, Any], *candidates: str) -> str | None:
    normalized_candidates = {_normalize_key(candidate) for candidate in candidates}
    for key in row.keys():
        if _normalize_key(key) in normalized_candidates:
            return key
    return None


def _coerce_number(value: Any) -> float | int | str:
    raw = str(value or "").strip()
    if not raw:
        return ""

    normalized = raw.replace("%", "").replace(" ", "")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")

    try:
        number = float(normalized)
    except ValueError:
        return raw

    if abs(number - round(number)) < 1e-9:
        return int(round(number))
    return number


def _format_value(value: float | int | str, *, is_percent: bool) -> str:
    if value == "":
        return ""

    if isinstance(value, (int, float)):
        number = float(value)
        if is_percent:
            pct = number * 100 if abs(number) <= 1 else number
            return f"{int(round(pct))}%"
        if abs(number - round(number)) < 1e-9:
            return str(int(round(number)))
        return f"{number:.2f}".replace(".", ",")

    return str(value)


def _sheet_csv_url(spreadsheet_id: str, sheet_name: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={quote(sheet_name)}"


def _get_secret_str(key: str, default: str = "") -> str:
    try:
        value = st.secrets.get(key, default)
    except Exception:
        return default
    return str(value).strip() if value is not None else default


def _sheet_values_api_url(spreadsheet_id: str, sheet_name: str, api_key: str) -> str:
    range_name = f"'{sheet_name}'"
    params = urlencode(
        {
            "key": api_key,
            "majorDimension": "ROWS",
            "valueRenderOption": "UNFORMATTED_VALUE",
            "dateTimeRenderOption": "FORMATTED_STRING",
        }
    )
    return f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{quote(range_name, safe='')}?{params}"


def _rows_from_values(values: list[list[Any]]) -> list[dict[str, Any]]:
    if not values:
        return []

    headers = [str(value).strip() for value in values[0]]
    rows: list[dict[str, Any]] = []
    for value_row in values[1:]:
        row = {
            headers[index]: value_row[index] if index < len(value_row) else ""
            for index in range(len(headers))
            if headers[index]
        }
        if any(str(value).strip() for value in row.values()):
            rows.append(row)
    return rows


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _read_sheet_rows_csv(spreadsheet_id: str, sheet_name: str) -> list[dict[str, Any]]:
    response = requests.get(_sheet_csv_url(spreadsheet_id, sheet_name), timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    text = response.text.lstrip("\ufeff")
    return list(DictReader(StringIO(text)))


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _read_sheet_rows_api(spreadsheet_id: str, sheet_name: str, api_key: str) -> list[dict[str, Any]]:
    response = requests.get(_sheet_values_api_url(spreadsheet_id, sheet_name, api_key), timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    values = payload.get("values")
    if not isinstance(values, list):
        return []
    return _rows_from_values(values)


def _read_sheet_rows(spreadsheet_id: str, sheet_name: str) -> list[dict[str, Any]]:
    api_key = _get_secret_str("GOOGLE_SHEETS_API_KEY")
    if api_key:
        return _read_sheet_rows_api(spreadsheet_id, sheet_name, api_key)
    return _read_sheet_rows_csv(spreadsheet_id, sheet_name)


def _build_cards(rows: list[dict[str, Any]], area: str | None = None) -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {
        key: {"titulo": title, "itens": []}
        for key, title in CARD_TITLES.items()
    }

    for row in rows:
        indicator_col = _find_column(row, "INDICADORES", "INDICADOR")
        value_col = _find_column(row, "VALOR", "VALUE")
        stage_col = _find_column(row, "ETAPA", "STAGE")
        date_col = _find_column(row, "DATA_ATUALIZACAO", "DATA ATUALIZACAO", "DATA_ATUALIZAÇÃO")
        area_col = _find_column(row, "AREA", "ÁREA")

        if not indicator_col or not value_col or not stage_col:
            continue

        if area and area_col and _normalize_key(row.get(area_col)) != _normalize_key(area):
            continue

        indicator = str(row.get(indicator_col) or "").strip()
        stage = _normalize_key(row.get(stage_col))
        card_key = STAGE_TO_CARD.get(stage)
        if not indicator or not card_key:
            continue

        value = _coerce_number(row.get(value_col))
        is_percent = _normalize_key(indicator) in PERCENT_INDICATORS
        cards[card_key]["itens"].append(
            {
                "indicador": indicator,
                "valor": value,
                "formattedValue": _format_value(value, is_percent=is_percent),
                "isPercent": is_percent,
                "dataAtualizacao": str(row.get(date_col) or "").strip() if date_col else "",
            }
        )

    return cards


def _latest_update(rows: list[dict[str, str]]) -> str | None:
    values: list[str] = []
    for row in rows:
        date_col = _find_column(row, "DATA_ATUALIZACAO", "DATA ATUALIZACAO", "DATA_ATUALIZAÇÃO")
        if date_col and str(row.get(date_col) or "").strip():
            values.append(str(row.get(date_col)).strip())
    return max(values) if values else None


def fetch_dashboard_payload(
    url: str = "",
    token: str = "",
    sheet: str = "INDICADORES_DASH_FICTICIO",
    area: str | None = None,
    spreadsheet_id: str = DEFAULT_DASHBOARD_SPREADSHEET_ID,
) -> Dict[str, Any]:
    try:
        rows = _read_sheet_rows(spreadsheet_id, sheet)
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "desconhecido"
        return {"ok": False, "message": f"Erro HTTP {status_code} ao ler o Google Sheets diretamente."}
    except Exception as exc:
        return {"ok": False, "message": f"Erro ao ler o Google Sheets diretamente: {exc}"}

    cards = _build_cards(rows, area=area)
    return {
        "ok": True,
        "cards": cards,
        "sheet": sheet,
        "spreadsheetName": "DashboardOmissao",
        "updatedAt": _latest_update(rows),
    }
