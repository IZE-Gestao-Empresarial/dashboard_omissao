from __future__ import annotations

from pathlib import Path
import re
import streamlit as st


_BASE_DIR = Path(__file__).resolve().parent.parent


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_asset_text(rel_path: str) -> str:
    path = _BASE_DIR / rel_path
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return _read_text(path)


def inject_kiosk_css() -> None:
    css = load_asset_text("assets/kiosk.css")
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


def render_dashboard(slots: dict[str, str], meta: dict[str, str | None] | None = None) -> str:
    template = load_asset_text("templates/dashboard.html")
    dashboard_css = load_asset_text("assets/dashboard.css")
    card_base_css = load_asset_text("assets/card_base.css")
    card_rotina_css = load_asset_text("assets/card_rotina.css")
    card_atualizacao_css = load_asset_text("assets/card_atualizacao.css")
    card_avancado_css = load_asset_text("assets/card_avancado.css")
    card_entregas_finais_css = load_asset_text("assets/card_entregas_finais.css")

    composed_css = f"{dashboard_css}\n\n{card_base_css}\n\n{card_atualizacao_css}\n\n{card_rotina_css}\n\n{card_avancado_css}\n\n{card_entregas_finais_css}"
    html_out = template.replace("__DASHBOARD_CSS__", composed_css)

    meta = meta or {}
    replacements = {
        "DASHBOARD_TITLE": meta.get("title") or "Dashboard de Omissão",
        "DASHBOARD_SHEET": meta.get("sheet") or "-",
        "DASHBOARD_UPDATED_AT": meta.get("updated_at") or "-",
    }

    for key, value in {**slots, **replacements}.items():
        html_out = html_out.replace(f"__{key}__", value)

    html_out = re.sub(r"__[^_]+__", "", html_out)
    return html_out
