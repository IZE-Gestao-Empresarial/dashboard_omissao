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
    "DASHS TRAVADOS POR PDC",
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



def _render_base_section(section: dict[str, Any], updated_at: str | None = None) -> str:
    items = section.get("itens") or []

    clientes_ativos = next((item for item in items if str(item.get("indicador") or "").strip().upper() == "CLIENTES ATIVOS"), None)
    metric_items = [
        item for item in items
        if str(item.get("indicador") or "").strip().upper() != "CLIENTES ATIVOS"
    ][:3]

    active_value = escape(str(clientes_ativos.get("formattedValue") or clientes_ativos.get("valor") or "-")) if clientes_ativos else "-"

    cards_html = []
    color_classes = ["base-metric-card--fc", "base-metric-card--dre", "base-metric-card--ind"]
    for idx, item in enumerate(metric_items):
        label = _normalize_base_label(str(item.get("indicador") or "-"))
        value = _split_metric_value(item)
        color_class = color_classes[idx] if idx < len(color_classes) else ""
        cards_html.append(
            f"""
            <article class="base-metric-card {color_class}">
              <div class="base-metric-percent">%</div>
              <div class="base-metric-value">{value}</div>
              <div class="base-metric-label">{escape(label)}</div>
            </article>
            """.strip()
        )

    while len(cards_html) < 3:
        cards_html.append(
            """
            <article class="base-metric-card">
              <div class="base-metric-percent">%</div>
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
            <div class="base-active-value">{active_value}</div>
            <div class="base-active-label">Qnt. Clientes ativos</div>
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



def _render_rotina_metric_card(item: dict[str, Any] | None, *, caption: str, theme_class: str) -> str:
    value = _split_metric_value(item or {}) if item else "-"
    percent_html = '<span class="rotina-metric-percent">%</span>' if value != '-' else ''
    return f"""
    <article class="rotina-metric-card {theme_class}">
      <div class="rotina-metric-main">
        <span class="rotina-metric-value">{value}</span>
        {percent_html}
      </div>
      <div class="rotina-metric-label">{escape(caption)}</div>
    </article>
    """.strip()



def _render_rotina_section(section: dict[str, Any], updated_at: str | None = None) -> str:
    items = section.get("itens") or []

    grupos_ativos = _find_item_by_predicate(
        items,
        lambda label: "GRUPO" in label and "ATIV" in label,
    )
    geral_3_dias = _find_item_by_predicate(
        items,
        lambda label: "GERAL" in label and "3" in label,
    )
    consultor_3_dias = _find_item_by_predicate(
        items,
        lambda label: "CONSULT" in label and "3" in label,
    )
    geral_5_dias = _find_item_by_predicate(
        items,
        lambda label: "GERAL" in label and "5" in label,
    )
    consultor_5_dias = _find_item_by_predicate(
        items,
        lambda label: "CONSULT" in label and "5" in label,
    )

    raw_title = str(section.get("titulo") or "").strip()
    title = "Termômetro de churn" if raw_title.upper() in {"", "ROTINA"} else escape(raw_title)
    grupos_ativos_valor = escape(
        str(grupos_ativos.get("formattedValue") or grupos_ativos.get("valor") or "-").replace("%", "").strip()
    ) if grupos_ativos else "-"

    footer = f'<div class="section-footer rotina-section-footer">Última atualização geral: {escape(updated_at)}</div>' if updated_at else ""

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
          <div class="rotina-matrix">
            <div class="rotina-row-label">3 Dias</div>
            {_render_rotina_metric_card(geral_3_dias, caption="Geral", theme_class="rotina-metric-card--light")}
            {_render_rotina_metric_card(consultor_3_dias, caption="Consultor", theme_class="rotina-metric-card--dark")}
            <div class="rotina-row-label">5 Dias</div>
            {_render_rotina_metric_card(geral_5_dias, caption="Geral", theme_class="rotina-metric-card--black")}
            {_render_rotina_metric_card(consultor_5_dias, caption="Consultor", theme_class="rotina-metric-card--orange")}
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



def _render_entregas_group(*, title: str, metric_a_html: str, metric_b_html: str) -> str:
    return f"""
    <article class="entregas-group">
      <div class="entregas-group-title">{escape(title)}</div>
      <div class="entregas-group-card">
        {metric_a_html}
        {metric_b_html}
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
    dashs_nao_atualizados = _find_item_by_predicate(
        items,
        lambda label: "DASH" in label and "ATUALIZ" in label,
    )
    travados_pdc = _find_item_by_predicate(
        items,
        lambda label: "TRAV" in label and ("PDC" in label or "P D C" in label),
    )

    footer = f'<div class="section-footer entregas-section-footer">Última atualização geral: {escape(updated_at)}</div>' if updated_at else ""

    relatorio_mensal_html = _render_entregas_group(
        title="Relatório Mensal",
        metric_a_html=_render_entregas_metric(relatorios_enviados, label="% Relatórios\nEnviados"),
        metric_b_html=_render_entregas_metric(excecoes_relatorio, label="% Exceções\nRelatório"),
    )
    radar_financeiro_html = _render_entregas_group(
        title="Radar Financeiro",
        metric_a_html=_render_entregas_metric(radar_enviados, label="% Radar\nEnviados"),
        metric_b_html=_render_entregas_metric(nao_elegiveis, label="% Não\nElegíveis"),
    )
    dashboard_html = _render_entregas_group(
        title="Dashboard 4.0",
        metric_a_html=_render_entregas_metric(dashs_nao_atualizados, label="% Dashs não\natualizados"),
        metric_b_html=_render_entregas_metric(travados_pdc, label="% Travados\npor pdc"),
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
          <div class="entregas-groups">
            {relatorio_mensal_html}
            {radar_financeiro_html}
            {dashboard_html}
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
