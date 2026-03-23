# DashboardOmissao (Streamlit)

Dashboard Streamlit conectado ao Apps Script do Google Sheets, usando a aba `INDICADORES_DASH_FICTICIO`.

## O que foi mantido
- layout do dashboard
- responsividade baseada no protótipo
- atualização automática a cada 5 minutos

## O que foi removido
- referências ao Dashboard Comercial
- indicadores, helpers e módulos que pertenciam ao projeto comercial antigo
- segredos antigos apontando para outras planilhas

## Secrets esperados
Crie `.streamlit/secrets.toml` com:

```toml
SHEETS_WEBAPP_URL = "https://script.google.com/macros/s/SEU_WEBAPP/exec"
SHEETS_WEBAPP_TOKEN = "SEU_TOKEN"
SHEETS_WEBAPP_SHEET = "INDICADORES_DASH_FICTICIO"
```

## Rodar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Formato esperado do JSON
O app espera um JSON com `ok`, `updatedAt` e `cards`, onde `cards` contém:
- `base`
- `atualizacao`
- `rotina`
- `avancado`
- `entrega_final`

Cada seção deve ter:
```json
{
  "titulo": "Base",
  "itens": [
    {
      "indicador": "FC",
      "valor": 0.82,
      "formattedValue": "82,1%",
      "isPercent": true,
      "dataAtualizacao": "2026-03-17 16:00:54"
    }
  ]
}
```


## Downloads nativos
Os downloads detalhados usam `st.download_button` nativo do Streamlit com chamada ao Apps Script no clique.
