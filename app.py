from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
from streamlit_autorefresh import st_autorefresh

from core.data import fetch_dashboard_payload
from core.downloads import get_download_bytes, get_download_spec
from ui.render import inject_kiosk_css, render_dashboard
from ui.section_card import omission_section_html


REFRESH_MS = 5 * 60 * 1000
DEFAULT_SHEET = "INDICADORES_DASH_FICTICIO"


def hide_streamlit_chrome() -> None:
    st.markdown(
        """
        <style>
          #MainMenu { visibility: hidden; }
          footer { visibility: hidden; }
          header { visibility: hidden; }
          [data-testid="stHeader"] { display: none !important; }
          [data-testid="stToolbar"] { display: none !important; }
          [data-testid="stDecoration"] { display: none !important; }
          [data-testid="stStatusWidget"] { display: none !important; }
          .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
          [data-testid="stAppViewContainer"] { padding-top: 0rem !important; }
          a[href*="streamlit.io"] { display: none !important; }
          iframe[title="streamlit"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_secret(key: str, default: str = "") -> str:
    try:
        value = st.secrets.get(key, default)
    except Exception:
        return default
    return str(value).strip() if value is not None else default


def inject_download_overlay_css() -> None:
    st.markdown(
        """
        <style>
          :root {
            --overlay-design-w: 1920;
            --overlay-design-h: 1080;

            /* Variáveis para ajustar apenas a posição X de cada botão do Streamlit */
            --overlay-dl-base-x: 169;
            --overlay-dl-atualizacao-x: 1036;
            --overlay-dl-rotina-x: 1265;
            --overlay-dl-avancado-x: 246;
            --overlay-dl-entrega-final-x: 1130;
          }

          [data-testid="stAppViewContainer"] > .main {
            overflow: hidden;
          }

          .st-key-area_filter {
            position: fixed;
            left: calc((420 / 1920) * 100vw);
            top: calc((68 / 1080) * 100vh);
            width: auto;
            z-index: 1001;
          }

          .st-key-area_filter label,
          .st-key-area_filter [data-testid="InputInstructions"],
          .st-key-area_filter [data-baseweb="select"] > div:first-child > div:last-child svg {
            display: none !important;
          }

          .st-key-area_filter [data-baseweb="select"] > div:first-child {
            background: var(--pill-bg, rgba(255,255,255,0.78)) !important;
            border: none !important;
            border-radius: 999px !important;
            height: 5.185vmin !important;
            min-height: unset !important;
            padding: 0 6vmin !important;
            box-shadow: none !important;
            gap: 0.926vmin !important;
            cursor: pointer !important;
          }

          .st-key-area_filter [data-baseweb="select"] > div:first-child:hover,
          .st-key-area_filter [data-baseweb="select"] > div:first-child:focus-within {
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
          }

          .st-key-area_filter [data-baseweb="select"] span,
          .st-key-area_filter [data-baseweb="select"] [data-testid="stSelectbox"],
          .st-key-area_filter [data-baseweb="select"] > div:first-child > div:first-child,
          .st-key-area_filter [data-baseweb="select"] > div:first-child > div:first-child * {
            color: #4a4a4a !important;
            font-family: "Inter", system-ui, sans-serif !important;
            font-size: 2.96vmin !important;
            font-weight: 400 !important;
            line-height: 1 !important;
            letter-spacing: -0.01em !important;
            padding: 0 !important;
            white-space: nowrap !important;
            transform: translateY(4.5px) !important;
          }

          .st-key-area_filter [data-baseweb="select"] svg {
            color: #6d6d6d !important;
            width: calc((22 / 1080) * 100vh) !important;
            height: calc((22 / 1080) * 100vh) !important;
            flex-shrink: 0 !important;
          }

          .st-key-area_filter [data-baseweb="popover"] [data-baseweb="menu"] {
            border-radius: calc((20 / 1080) * 100vh) !important;
            border: none !important;
            box-shadow: 0 4px 24px rgba(0,0,0,0.10) !important;
            background: rgba(255,255,255,0.97) !important;
            margin-top: calc((8 / 1080) * 100vh) !important;
          }

          .st-key-area_filter [data-baseweb="popover"] [role="option"] {
            font-family: "Inter", system-ui, sans-serif !important;
            font-size: calc((28 / 1080) * 100vh) !important;
            font-weight: 400 !important;
            color: #4a4a4a !important;
            border-radius: calc((12 / 1080) * 100vh) !important;
          }

          .st-key-area_filter [data-baseweb="popover"] [role="option"]:hover,
          .st-key-area_filter [data-baseweb="popover"] [aria-selected="true"] {
            background: rgba(0,0,0,0.05) !important;
          }

          .st-key-dl_base,
          .st-key-dl_atualizacao,
          .st-key-dl_rotina,
          .st-key-dl_avancado,
          .st-key-dl_entrega_final {
            position: fixed;
            z-index: 1000;
          }

          .st-key-dl_base {
            left: calc((var(--overlay-dl-base-x) / var(--overlay-design-w)) * 100vw);
            top: calc((68 / var(--overlay-design-h)) * 100vh);
          }

          .st-key-dl_atualizacao {
            left: calc((var(--overlay-dl-atualizacao-x) / var(--overlay-design-w)) * 100vw);
            top: calc((164 / var(--overlay-design-h)) * 100vh);
          }

          .st-key-dl_rotina {
            left: calc((var(--overlay-dl-rotina-x) / var(--overlay-design-w)) * 100vw);
            top: calc((68 / var(--overlay-design-h)) * 100vh);
          }

          .st-key-dl_avancado {
            left: calc((var(--overlay-dl-avancado-x) / var(--overlay-design-w)) * 100vw);
            top: calc((674 / var(--overlay-design-h)) * 100vh);
          }

          .st-key-dl_entrega_final {
            left: calc((var(--overlay-dl-entrega-final-x) / var(--overlay-design-w)) * 100vw);
            top: calc((674 / var(--overlay-design-h)) * 100vh);
          }

          .st-key-dl_base [data-testid="stDownloadButton"],
          .st-key-dl_atualizacao [data-testid="stDownloadButton"],
          .st-key-dl_rotina [data-testid="stDownloadButton"],
          .st-key-dl_avancado [data-testid="stDownloadButton"],
          .st-key-dl_entrega_final [data-testid="stDownloadButton"] {
            margin: 0 !important;
          }

          .st-key-dl_base [data-testid="stDownloadButton"] button,
          .st-key-dl_atualizacao [data-testid="stDownloadButton"] button,
          .st-key-dl_rotina [data-testid="stDownloadButton"] button,
          .st-key-dl_avancado [data-testid="stDownloadButton"] button,
          .st-key-dl_entrega_final [data-testid="stDownloadButton"] button {
            width: min(56px, calc((56 / var(--overlay-design-w)) * 100vw));
            min-width: min(56px, calc((56 / var(--overlay-design-w)) * 100vw));
            height: min(56px, calc((56 / var(--overlay-design-h)) * 100vh));
            min-height: min(56px, calc((56 / var(--overlay-design-h)) * 100vh));
            border-radius: 999px;
            border: none !important;
            background: transparent !important;
            color: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
            font-size: 1px !important;
            line-height: 1 !important;
            outline: none !important;
          }

          .st-key-dl_base [data-testid="stDownloadButton"] button:hover,
          .st-key-dl_atualizacao [data-testid="stDownloadButton"] button:hover,
          .st-key-dl_rotina [data-testid="stDownloadButton"] button:hover,
          .st-key-dl_avancado [data-testid="stDownloadButton"] button:hover,
          .st-key-dl_entrega_final [data-testid="stDownloadButton"] button:hover,
          .st-key-dl_base [data-testid="stDownloadButton"] button:active,
          .st-key-dl_atualizacao [data-testid="stDownloadButton"] button:active,
          .st-key-dl_rotina [data-testid="stDownloadButton"] button:active,
          .st-key-dl_avancado [data-testid="stDownloadButton"] button:active,
          .st-key-dl_entrega_final [data-testid="stDownloadButton"] button:active {
            background: transparent !important;
            box-shadow: none !important;
            border: none !important;
          }

          .st-key-dl_base [data-testid="stDownloadButton"] button p,
          .st-key-dl_atualizacao [data-testid="stDownloadButton"] button p,
          .st-key-dl_rotina [data-testid="stDownloadButton"] button p,
          .st-key-dl_avancado [data-testid="stDownloadButton"] button p,
          .st-key-dl_entrega_final [data-testid="stDownloadButton"] button p,
          .st-key-dl_base [data-testid="stDownloadButton"] button svg,
          .st-key-dl_atualizacao [data-testid="stDownloadButton"] button svg,
          .st-key-dl_rotina [data-testid="stDownloadButton"] button svg,
          .st-key-dl_avancado [data-testid="stDownloadButton"] button svg,
          .st-key-dl_entrega_final [data-testid="stDownloadButton"] button svg {
            opacity: 0 !important;
            color: transparent !important;
          }

          @media (max-width: 960px) and (max-height: 540px) {
            .st-key-area_filter {
              display: none !important;
              visibility: hidden !important;
              pointer-events: none !important;
            }

            .st-key-dl_base,
            .st-key-dl_atualizacao,
            .st-key-dl_rotina,
            .st-key-dl_avancado,
            .st-key-dl_entrega_final {
              display: none !important;
              visibility: hidden !important;
              pointer-events: none !important;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_download_overlays(updated_at: str | None = None, area: str | None = None) -> None:
    overlay_order = ["base", "atualizacao", "rotina", "avancado", "entrega_final"]

    for key in overlay_order:
        spec = get_download_spec(key, updated_at=updated_at)
        file_bytes = get_download_bytes(key, area=area)
        st.download_button(
            label=" ",
            data=file_bytes,
            file_name=spec["filename"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{key}",
            help=f"Baixar detalhamento {spec['label']}",
            on_click="ignore",
            type="tertiary",
            width=56,
        )


# FIX: set_page_config deve ser a primeira chamada Streamlit
st.set_page_config(page_title="Dashboard de Omissão", layout="wide")
hide_streamlit_chrome()
inject_kiosk_css()
inject_download_overlay_css()
st_autorefresh(interval=REFRESH_MS, key="dashboard-omissao-refresh")

url = _get_secret("SHEETS_WEBAPP_URL")
token = _get_secret("SHEETS_WEBAPP_TOKEN")
sheet_name = _get_secret("SHEETS_WEBAPP_SHEET", DEFAULT_SHEET)

if not url or not token:
    st.error(
        "Configure SHEETS_WEBAPP_URL e SHEETS_WEBAPP_TOKEN no .streamlit/secrets.toml para carregar o DashboardOmissao."
    )
    st.stop()

if "selected_area" not in st.session_state:
    st.session_state.selected_area = None

AREA_OPTIONS = ["Todos", "Produto", "Serviço", "Markup"]

# Lê query param ?area_filter= enviado pelo tv_rotation.html
_area_from_url = urllib.parse.unquote(str(st.query_params.get("area_filter", ""))).strip()
_default_index = (
    AREA_OPTIONS.index(_area_from_url)
    if _area_from_url in AREA_OPTIONS
    else 0
)

st.selectbox(
    label="Filtrar por Área",
    options=AREA_OPTIONS,
    index=_default_index,
    key="area_filter",
    label_visibility="collapsed",
)

area_filter_value = st.session_state.get("area_filter", "Todos")
selected_area = None if area_filter_value == "Todos" else area_filter_value

payload = fetch_dashboard_payload(url=url, token=token, sheet=sheet_name, area=selected_area)

print("DEBUG area:", selected_area)
print("DEBUG sheet:", payload.get("sheet"))
itens_base = payload.get("cards", {}).get("base", {}).get("itens", [])
clientes_ativos = next((i["valor"] for i in itens_base if i["indicador"] == "CLIENTES ATIVOS"), "não encontrado")
print("DEBUG clientes_ativos:", clientes_ativos)

if not payload.get("ok"):
    error_message = payload.get("message") or payload.get("error") or "Falha ao carregar o dashboard."
    st.error(f"Erro ao carregar dados do DashboardOmissao: {error_message}")
    st.json(payload)
    st.stop()

cards = payload.get("cards", {})
updated_at = payload.get("updatedAt")
source_sheet = payload.get("sheet") or sheet_name
spreadsheet_name = payload.get("spreadsheetName") or "DashboardOmissao"

slots = {
    "CARD_BASE": omission_section_html(
        cards.get("base", {}),
        section_class="section--base",
        updated_at=updated_at,
    ),
    "CARD_ATUALIZACAO": omission_section_html(
        cards.get("atualizacao", {}),
        section_class="section--atualizacao",
        header_align="center",
        updated_at=updated_at,
    ),
    "CARD_ROTINA": omission_section_html(
        cards.get("rotina", {}),
        section_class="section--rotina",
        updated_at=updated_at,
    ),
    "CARD_AVANCADO": omission_section_html(
        cards.get("avancado", {}),
        section_class="section--avancado",
        updated_at=updated_at,
    ),
    "CARD_ENTREGAS_FINAIS": omission_section_html(
        cards.get("entrega_final", {}),
        section_class="section--entregas-finais",
        updated_at=updated_at,
    ),
}

html = render_dashboard(
    slots=slots,
    meta={
        "title": spreadsheet_name,
        "sheet": source_sheet,
        "updated_at": updated_at,
    },
)
components.html(html, height=1, scrolling=False)

render_download_overlays(updated_at=updated_at, area=selected_area)