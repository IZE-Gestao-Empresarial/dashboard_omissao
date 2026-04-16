from __future__ import annotations

from html import escape
from typing import Any
import math


PERCENT_LABELS = {
    "FC",
    "DRE",
    "INDICADORES",
    "GERAL - 3 DIAS",
    "CONSULTOR - 3 DIAS",
    "GERAL - 5 DIAS",
    "CONSULTOR - 5 DIAS",
    "OBJETIVOS ESTRATÉGICOS",
    "PLANEJAMENTO ESTRATÉGICO",
    "TERMÔMETRO INDICADORES",
    "RELATÓRIOS ENVIADOS",
    "EXCEÇÕES RELATÓRIOS",
    "RADAR ENVIADOS",
    "NÃO ELEGÍVEIS RADAR",
    "DASHS NÃO ATUALIZADOS",
    "DASHBOARDS ATUALIZADOS",
    "DASHS ATUALIZADOS",
    "DASHS TRAVADOS POR PDC",
    "RESUMO REUNIÃO",
}


def _badge_class(item: dict[str, Any]) -> str:
    label = str(item.get("indicador") or "").strip().upper()
    value = item.get("valor")

    if label in {"EXCEÇÕES RELATÓRIOS", "GERAL - 5 DIAS", "CONSULTOR - 5 DIAS", "DASHS NÃO ATUALIZADOS", "DASHS TRAVADOS POR PDC"}:
        return "metric-badge metric-badge--risk"

    if isinstance(value, (int, float)) and value >= 1 and label in PERCENT_LABELS:
        return "metric-badge metric-badge--highlight"

    return "metric-badge"



def _render_item(item: dict[str, Any]) -> str:
    indicador = escape(str(item.get("indicador") or "-"))
    formatted = _format_metric_value(item, include_suffix=True)
    updated = item.get("dataAtualizacao")
    meta = f'<div class="metric-meta">Atualizado em {escape(str(updated))}</div>' if updated else ""

    return f"""
    <article class="metric-row">
      <div class="metric-copy">
        <div class="metric-label">{indicador}</div>
        {meta}
      </div>
      <div class="{_badge_class(item)}">{formatted}</div>
    </article>
    """.strip()



def _normalize_base_label(label: str) -> str:
    label_up = (label or "").strip().upper()
    if label_up == "INDICADORES":
        return "IND"
    return label_up



def _split_metric_value(item: dict[str, Any]) -> str:
    return _format_metric_value(item, include_suffix=False)



def _extract_numeric_value(item: dict[str, Any] | None) -> float | None:
    if not item:
        return None

    raw_value = item.get("valor")
    if isinstance(raw_value, (int, float)):
        return float(raw_value)

    formatted = str(item.get("formattedValue") or raw_value or "").strip()
    if not formatted:
        return None

    normalized = formatted.replace("%", "").replace(" ", "").strip()
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")

    try:
        return float(normalized)
    except ValueError:
        return None



def _format_plain_number(value: float | None) -> str:
    if value is None:
        return "-"

    if abs(value - round(value)) < 1e-9:
        text = f"{int(round(value)):,}".replace(",", ".")
        return escape(text)

    text = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return escape(text)



def _format_percent_number(value: float | None) -> str:
    if value is None:
        return "-"

    text = f"{value:,.2f}%".replace(",", "_").replace(".", ",").replace("_", ".")
    return escape(text)



def _is_total_base_item(label: str) -> bool:
    normalized = _normalize_lookup_label(label)
    return "BASE" in normalized and "TOTAL" in normalized and "CLIENT" in normalized



def _render_base_section(section: dict[str, Any], updated_at: str | None = None) -> str:
    items = section.get("itens") or []

    clientes_ativos = _find_item_by_predicate(items, lambda label: label == "CLIENTES ATIVOS")
    total_base_clientes = _find_item_by_predicate(items, _is_total_base_item)

    fc_item = _find_item_by_predicate(items, lambda label: label == "FC" or " FC" in label or label.startswith("FC "))
    dre_item = _find_item_by_predicate(items, lambda label: label == "DRE" or " DRE" in label or label.startswith("DRE "))
    ind_item = _find_item_by_predicate(items, lambda label: label == "INDICADORES" or label == "IND" or "INDIC" in label)

    metric_items = [fc_item, dre_item, ind_item]

    active_value = escape(str(clientes_ativos.get("formattedValue") or clientes_ativos.get("valor") or "-")) if clientes_ativos else "-"
    total_base_value = _format_plain_number(_extract_numeric_value(total_base_clientes))

    clientes_ativos_num = _extract_numeric_value(clientes_ativos)
    total_base_num = _extract_numeric_value(total_base_clientes)
    cobertura_value = None
    if clientes_ativos_num is not None and total_base_num not in (None, 0):
        cobertura_value = (clientes_ativos_num / total_base_num) * 100.0
    cobertura_display = _format_percent_number(cobertura_value)

    cards_html = []
    color_classes = ["base-metric-card--fc", "base-metric-card--dre", "base-metric-card--ind"]
    for idx, item in enumerate(metric_items):
        label = _normalize_base_label(str((item or {}).get("indicador") or "-"))
        value = _format_metric_value(item or {}, include_suffix=True) if item else "-"
        color_class = color_classes[idx] if idx < len(color_classes) else ""
        cards_html.append(
            f"""
            <article class="base-metric-card {color_class}">
              <div class="base-metric-value">{value}</div>
              <div class="base-metric-label">{escape(label)}</div>
            </article>
            """.strip()
        )

    while len(cards_html) < 3:
        cards_html.append(
            """
            <article class="base-metric-card">
              <div class="base-metric-value">-</div>
              <div class="base-metric-label">-</div>
            </article>
            """.strip()
        )

    footer = f'<div class="section-footer base-section-footer">Última atualização geral: {escape(updated_at)}</div>' if updated_at else ""

    return f"""
    <section class="omission-section section--base">
      <div class="section-header section-header--base-placeholder">
        <div class="section-pill">Base</div>
        <button class="section-download" type="button">
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M12 4v9"></path>
            <path d="M8.5 10.5 12 14l3.5-3.5"></path>
            <path d="M6 18h12"></path>
          </svg>
        </button>
      </div>
      <div class="section-card base-section-card">
        <div class="section-card-content base-section-content">
          <div class="base-prototype-title">Coração da operação</div>
          <div class="base-prototype-topline">
            <div class="base-top-stat">
              <div class="base-top-stat-value">{total_base_value}</div>
              <div class="base-top-stat-label">Base Total</div>
            </div>
            <div class="base-top-stat">
              <div class="base-top-stat-value">{active_value}</div>
              <div class="base-top-stat-label">Qnt. Clientes ativos</div>
            </div>
            <div class="base-top-stat">
              <div class="base-top-stat-value">{cobertura_display}</div>
              <div class="base-top-stat-label">Ativos / Base</div>
            </div>
          </div>
          <div class="base-prototype-metrics">
            {''.join(cards_html)}
          </div>
        </div>
        {footer}
      </div>
    </section>
    """.strip()





def _normalize_lookup_label(label: str) -> str:
    return " ".join((label or "").strip().upper().replace("_", " ").replace("-", " - ").split())



def _find_item_by_predicate(items: list[dict[str, Any]], predicate) -> dict[str, Any] | None:
    for item in items:
        label = _normalize_lookup_label(str(item.get("indicador") or ""))
        if predicate(label):
            return item
    return None



def _format_rotina_number(item: dict[str, Any] | None) -> str:
    return _format_plain_number(_extract_numeric_value(item))



def _render_rotina_metric_card(item: dict[str, Any] | None, *, caption: str, theme_class: str) -> str:
    value = _format_rotina_number(item)
    return f"""
    <article class="rotina-metric-card {theme_class}">
      <div class="rotina-metric-main">
        <span class="rotina-metric-value">{value}</span>
      </div>
      <div class="rotina-metric-label">{escape(caption)}</div>
    </article>
    """.strip()



def _render_rotina_section(section: dict[str, Any], updated_at: str | None = None) -> str:
    items = section.get("itens") or []


    grupos_ativos = _find_item_by_predicate(
            items,
            lambda label: ("GRUPO" in label and "ATIV" in label)
                          or ("WPP" in label and "ATIV" in label)
                          or ("WHATSAPP" in label and "ATIV" in label),
    )
    geral_inativos = _find_item_by_predicate(
        items,
        lambda label: "INATIV" in label,
    )
    resumo_reuniao = _find_item_by_predicate(
        items,
        lambda label: "RESUMO" in label and "REUNI" in label,
    )

    grupos_ativos_valor = _format_rotina_number(grupos_ativos)
    inativos_valor = _format_rotina_number(geral_inativos)
    inativos_label = escape(str((geral_inativos or {}).get("indicador") or "Geral - Inativos").strip())
    resumo_valor = _format_metric_value(resumo_reuniao, include_suffix=True)
    resumo_label = escape(str((resumo_reuniao or {}).get("indicador") or "Resumo Reunião").strip())

    footer = f'<div class="section-footer rotina-section-footer">Última atualização geral: {escape(updated_at)}</div>' if updated_at else ""

    raw_title = str(section.get("titulo") or "").strip()
    title = "Termômetro de churn" if raw_title.upper() in {"", "ROTINA"} else escape(raw_title)

    return f"""
    <section class="omission-section section--rotina">
      <div class="section-header section-header--rotina-placeholder">
        <div class="section-pill">Rotina</div>
        <button class="section-download" type="button">
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M12 4v9"></path>
            <path d="M8.5 10.5 12 14l3.5-3.5"></path>
            <path d="M6 18h12"></path>
          </svg>
        </button>
      </div>
      <div class="section-card rotina-section-card">
        <div class="section-card-content rotina-section-content">
          <div class="rotina-header">
            <div class="rotina-title">{title}</div>
            <div class="rotina-summary">
              <span class="rotina-summary-value">{grupos_ativos_valor}</span>
              <span class="rotina-summary-label">Grupos wpp ativos</span>
            </div>
          </div>
          <div class="rotina-blocks-row">
            <div class="rotina-inativos-card">
              <span class="rotina-metric-value">{inativos_valor}</span>
              <span class="rotina-metric-label">{inativos_label}</span>
            </div>
            <div class="rotina-reuniao-card">
              <span class="rotina-metric-value">{resumo_valor}</span>
              <span class="rotina-metric-label">{resumo_label}</span>
            </div>
          </div>
        </div>
        {footer}
      </div>
    </section>
    """.strip()




def _render_avancado_metric_card(item: dict[str, Any] | None, *, label: str) -> str:
    value = _split_metric_value(item or {}) if item else "-"
    percent_html = '<span class="avancado-value-percent">%</span>' if value != '-' else ''
    return f"""
    <article class="avancado-item">
      <div class="avancado-item-label">{escape(label)}</div>
      <div class="avancado-item-value">
        <span class="avancado-value-number">{value}</span>
        {percent_html}
      </div>
    </article>
    """.strip()


def _render_avancado_section(section: dict[str, Any], updated_at: str | None = None) -> str:
    items = section.get("itens") or []

    objetivos = _find_item_by_predicate(
        items,
        lambda label: "OBJETIVO" in label,
    )
    planejamento = _find_item_by_predicate(
        items,
        lambda label: "PLANEJAMENTO" in label,
    )
    termometro = _find_item_by_predicate(
        items,
        lambda label: "TERM" in label and "INDIC" in label,
    )

    raw_title = str(section.get("titulo") or "").strip()
    title = "Garantia de LTV e Estratégia" if raw_title.upper() in {"", "AVANCADO", "AVANÇADO"} else escape(raw_title)

    footer = f'<div class="section-footer avancado-section-footer">Última atualização geral: {escape(updated_at)}</div>' if updated_at else ""

    objetivos_label = "Objetivos\nEstratégicos"
    planejamento_label = "Planejamento\nEstratégico"
    termometro_label = "Termômetro\nIndicadores"

    objetivos_html = _render_avancado_metric_card(objetivos, label=objetivos_label)
    planejamento_html = _render_avancado_metric_card(planejamento, label=planejamento_label)
    termometro_html = _render_avancado_metric_card(termometro, label=termometro_label)

    return f"""
    <section class="omission-section section--avancado">
      <div class="section-header">
        <div class="section-pill">Avançado</div>
        <button class="section-download" aria-label="Atualização Avançado" title="Painel Avançado" type="button">
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M12 4v9"></path>
            <path d="M8.5 10.5 12 14l3.5-3.5"></path>
            <path d="M6 18h12"></path>
          </svg>
        </button>
      </div>
      <div class="section-card avancado-section-card">
        <div class="section-card-content avancado-section-content">
          <div class="avancado-title">{title}</div>
          <div class="avancado-grid">
            {objetivos_html}
            {planejamento_html}
            {termometro_html}
          </div>
        </div>
        {footer}
      </div>
    </section>
    """.strip()





def _is_percent_item(item: dict[str, Any] | None) -> bool:
    if not item:
        return False

    if bool(item.get("isPercent")):
        return True

    label = str(item.get("indicador") or "").strip().upper()
    if label in PERCENT_LABELS:
        return True

    formatted = str(item.get("formattedValue") or "").strip()
    return "%" in formatted



def _format_metric_value(item: dict[str, Any] | None, *, include_suffix: bool) -> str:
    if not item:
        return "-"

    if _is_percent_item(item):
        pct = int(round(_extract_percentage(item)))
        value = str(pct)
        if include_suffix:
            value += "%"
        return escape(value)

    formatted = str(item.get("formattedValue") or item.get("valor") or "-").strip()
    if include_suffix:
        return escape(formatted)

    if formatted.endswith("%"):
        formatted = formatted[:-1].strip()
    return escape(formatted)

def _render_entregas_metric(item: dict[str, Any] | None, *, label: str) -> str:
    value = _format_metric_value(item, include_suffix=True)
    return f"""
    <div class="entregas-metric">
      <div class="entregas-metric-label">{escape(label)}</div>
      <div class="entregas-metric-value">{value}</div>
    </div>
    """.strip()



def _render_entregas_panel(*, title: str, metrics_html: str, panel_class: str = "") -> str:
    panel_class_attr = f" entregas-panel--{panel_class.strip()}" if panel_class.strip() else ""
    return f"""
    <article class="entregas-panel{panel_class_attr}">
      <div class="entregas-panel-title">{escape(title)}</div>
      <div class="entregas-panel-card">
        {metrics_html}
      </div>
    </article>
    """.strip()




def _extract_percentage(item: dict[str, Any] | None) -> float:
    if not item:
        return 0.0

    raw_value = item.get("valor")
    label = str(item.get("indicador") or "").strip().upper()
    is_percent = bool(item.get("isPercent")) or label in PERCENT_LABELS

    if isinstance(raw_value, (int, float)):
        pct = float(raw_value) * 100.0 if is_percent and abs(float(raw_value)) <= 1 else float(raw_value)
        return max(0.0, min(100.0, pct))

    formatted = str(item.get("formattedValue") or raw_value or "").strip()
    if not formatted:
        return 0.0

    normalized = formatted.replace("%", "").replace(" ", "").strip()
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        pct = float(normalized)
    except ValueError:
        return 0.0
    return max(0.0, min(100.0, pct))


def _split_percent_display(item: dict[str, Any] | None) -> tuple[str, str]:
    pct = int(round(_extract_percentage(item)))
    return str(pct), "%"


def _render_atualizacao_gauge(item: dict[str, Any] | None, *, fallback_label: str) -> str:
    label = str((item or {}).get("indicador") or fallback_label or "-").strip().upper()
    value_text, suffix = _split_percent_display(item)
    pct = _extract_percentage(item)

    gauge_size = 156
    center = 78
    radius = 52
    dots = 16
    dot_radius = 6.8
    circumference = 2 * 3.141592653589793 * radius
    start_angle = 165
    step_angle = 360 / dots

    filled_dot_count = max(0, min(dots, math.floor((pct / 100.0) * dots)))
    first_unfilled_dot = max(0, min(dots, math.ceil((pct / 100.0) * dots)))

    # O preenchimento precisa parar antes da próxima bolinha vazia,
    # sem "encostar" nela visualmente.
    cap_compensation_angle = 0.0
    if 0 < filled_dot_count < dots:
        stroke_width = 12.0
        cap_extension = stroke_width / 2.0
        cap_compensation_angle = math.degrees(cap_extension / radius) + (step_angle * 0.18)

    snapped_sweep = max(0.0, (filled_dot_count / dots) * 360.0 - cap_compensation_angle)
    dash = circumference * (snapped_sweep / 360.0)

    dots_svg = []
    for index in range(dots):
        if index < first_unfilled_dot:
            continue

        angle_deg = start_angle + (step_angle * index)
        angle_rad = angle_deg * 3.141592653589793 / 180
        x = center + radius * math.cos(angle_rad)
        y = center + radius * math.sin(angle_rad)
        dots_svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{dot_radius}" class="atualizacao-gauge-dot" />')

    return f"""
    <article class="atualizacao-gauge">
      <div class="atualizacao-gauge-shell">
        <svg class="atualizacao-gauge-svg" viewBox="0 0 {gauge_size} {gauge_size}" aria-hidden="true" focusable="false">
          <circle
            cx="{center}"
            cy="{center}"
            r="{radius}"
            fill="none"
            class="atualizacao-gauge-fill"
            stroke-dasharray="{dash:.2f} {circumference:.2f}"
            transform="rotate({start_angle} {center} {center})"
          />
          {''.join(dots_svg)}
        </svg>
        <div class="atualizacao-gauge-center">
          <div class="atualizacao-gauge-value-row">
            <span class="atualizacao-gauge-value">{value_text}</span>
            <span class="atualizacao-gauge-value-suffix">{escape(suffix)}</span>
          </div>
          <div class="atualizacao-gauge-label">{escape(label)}</div>
        </div>
      </div>
    </article>
    """.strip()


def _render_atualizacao_section(section: dict[str, Any], updated_at: str | None = None) -> str:
    title = str(section.get("titulo") or "Atualização").strip() or "Atualização"
    items = section.get("itens") or []

    fc_item = _find_item_by_predicate(items, lambda label: label == "FC" or " FC" in label or label.startswith("FC "))
    dre_item = _find_item_by_predicate(items, lambda label: label == "DRE" or " DRE" in label or label.startswith("DRE "))

    ordered_items = []
    for item in (fc_item, dre_item):
        if item and item not in ordered_items:
            ordered_items.append(item)

    for item in items:
        if item not in ordered_items:
            ordered_items.append(item)

    while len(ordered_items) < 2:
        ordered_items.append(None)

    gauges_html = [
        _render_atualizacao_gauge(ordered_items[0], fallback_label="FC"),
        _render_atualizacao_gauge(ordered_items[1], fallback_label="DRE"),
    ]

    return f"""
    <section class="omission-section section--atualizacao">
      <div class="section-header section-header--center">
        <div class="section-pill">{escape(title)}</div>
      </div>
      <div class="section-card atualizacao-section-card">
        <button class="section-download atualizacao-download" aria-label="Atualização {escape(title)}" title="Painel {escape(title)}" type="button">
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M12 4v9"></path>
            <path d="M8.5 10.5 12 14l3.5-3.5"></path>
            <path d="M6 18h12"></path>
          </svg>
        </button>
        <div class="section-card-content atualizacao-section-content">
          <div class="atualizacao-gauges">
            {''.join(gauges_html)}
          </div>
        </div>
      </div>
    </section>
    """.strip()



def _render_entregas_finais_section(section: dict[str, Any], updated_at: str | None = None) -> str:
    items = section.get("itens") or []

    relatorios_enviados = _find_item_by_predicate(
        items,
        lambda label: "RELAT" in label and "ENVIAD" in label,
    )
    excecoes_relatorio = _find_item_by_predicate(
        items,
        lambda label: "EXCE" in label and "RELAT" in label,
    )
    radar_enviados = _find_item_by_predicate(
        items,
        lambda label: "RADAR" in label and "ENVIAD" in label,
    )
    nao_elegiveis = _find_item_by_predicate(
        items,
        lambda label: "ELEG" in label,
    )

    # indicador mudou: de "não atualizados" para "atualizados"
    dashs_atualizados = _find_item_by_predicate(
        items,
        lambda label: (
            "DASH" in label and "ATUALIZ" in label and "NAO" not in label and "NÃO" not in label
        ),
    )
    if not dashs_atualizados:
        dashs_atualizados = _find_item_by_predicate(
            items,
            lambda label: "DASHBOARD" in label and "ATUALIZ" in label,
        )

    travados_pdc = _find_item_by_predicate(
        items,
        lambda label: "TRAV" in label and ("PDC" in label or "P D C" in label),
    )

    footer = f'<div class="section-footer entregas-section-footer">Última atualização geral: {escape(updated_at)}</div>' if updated_at else ""

    entregas_metrics_html = "\n".join([
        _render_entregas_metric(relatorios_enviados, label="Relatórios\nEnviados"),
        _render_entregas_metric(radar_enviados, label="Radar\nEnviados"),
        _render_entregas_metric(dashs_atualizados, label="Dashboards\nAtualizados"),
    ])
    nao_entregas_metrics_html = "\n".join([
        _render_entregas_metric(excecoes_relatorio, label="Exceções\nRelatório"),
        _render_entregas_metric(nao_elegiveis, label="Não\nElegíveis Radar"),
        _render_entregas_metric(travados_pdc, label="Travados\npor pdc"),
    ])

    entregas_html = _render_entregas_panel(
        title="Entregas",
        metrics_html=f'<div class="entregas-panel-metrics entregas-panel-metrics--3">{entregas_metrics_html}</div>',
        panel_class="positive",
    )
    nao_entregas_html = _render_entregas_panel(
        title="Não Entregas",
        metrics_html=f'<div class="entregas-panel-metrics entregas-panel-metrics--3">{nao_entregas_metrics_html}</div>',
        panel_class="negative",
    )

    return f"""
    <section class="omission-section section--entregas-finais">
      <div class="section-header">
        <div class="section-pill">Entregas Finais</div>
        <button class="section-download" aria-label="Atualização Entregas Finais" title="Painel Entregas Finais" type="button">
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M12 4v9"></path>
            <path d="M8.5 10.5 12 14l3.5-3.5"></path>
            <path d="M6 18h12"></path>
          </svg>
        </button>
      </div>
      <div class="section-card entregas-section-card">
        <div class="section-card-content entregas-section-content">
          <div class="entregas-panels">
            {entregas_html}
            {nao_entregas_html}
          </div>
        </div>
        {footer}
      </div>
    </section>
    """.strip()


def omission_section_html(
    section: dict[str, Any],
    *,
    section_class: str = "",
    header_align: str = "left",
    updated_at: str | None = None,
) -> str:
    if section_class.strip() == "section--base":
        return _render_base_section(section, updated_at=updated_at)

    if section_class.strip() == "section--rotina":
        return _render_rotina_section(section, updated_at=updated_at)

    if section_class.strip() == "section--atualizacao":
        return _render_atualizacao_section(section, updated_at=updated_at)

    if section_class.strip() == "section--avancado":
        return _render_avancado_section(section, updated_at=updated_at)

    if section_class.strip() == "section--entregas-finais":
        return _render_entregas_finais_section(section, updated_at=updated_at)

    title = str(section.get("titulo") or "Seção")
    items = section.get("itens") or []

    extra_class = f" {section_class.strip()}" if section_class.strip() else ""
    align_class = f" section-header--{header_align.strip()}" if header_align.strip() else ""

    body = "\n".join(_render_item(item) for item in items) if items else '<div class="section-empty">Sem indicadores nesta seção.</div>'
    footer = f'<div class="section-footer">Última atualização geral: {escape(updated_at)}</div>' if updated_at else ""

    return f"""
    <section class="omission-section{extra_class}">
      <div class="section-header{align_class}">
        <div class="section-pill">{escape(title)}</div>
        <button class="section-download" aria-label="Atualização {escape(title)}" title="Painel {escape(title)}" type="button">
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M12 4v9"></path>
            <path d="M8.5 10.5 12 14l3.5-3.5"></path>
            <path d="M6 18h12"></path>
          </svg>
        </button>
      </div>
      <div class="section-card">
        <div class="section-card-content">{body}</div>
        {footer}
      </div>
    </section>
    """.strip()
