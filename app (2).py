import streamlit as st
from datetime import date
import math

# ══════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════
st.set_page_config(
    page_title="Pagaré USD — Rosental S.A.",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════
# CUSTOM CSS
# ══════════════════════════════════════════════════
st.markdown("""
<style>
/* Background */
[data-testid="stAppViewContainer"] > .main { background: #f0f2f7; }
[data-testid="block-container"] { padding-top: 1rem; padding-bottom: 2rem; }

/* Hide default Streamlit header/footer */
#MainMenu, header, footer { visibility: hidden; }

/* App header */
.app-header {
    background: linear-gradient(135deg, #0f2d5e 0%, #1a4fa8 100%);
    color: white;
    padding: 20px 28px;
    border-radius: 12px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.app-header h1 { font-size: 1.35rem; margin: 0; font-weight: 700; }
.app-header p  { font-size: 0.78rem; opacity: 0.7; margin: 4px 0 0; }

/* Section label */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    color: #64748b;
    margin-bottom: 6px;
}

/* Param card */
.param-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px 18px;
}
.param-card h4 {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #6b7280;
    margin: 0 0 10px 0;
}

/* Words hint */
.words-hint {
    font-size: 0.71rem;
    color: #9ca3af;
    font-style: italic;
    margin-top: -10px;
    padding-bottom: 2px;
    min-height: 16px;
    line-height: 1.3;
}

/* Number input blue highlight */
[data-testid="stNumberInput"] input {
    font-weight: 600;
    color: #1a4fa8;
}

/* Results table */
.results-table-wrapper {
    overflow-x: auto;
    border-radius: 10px;
    border: 1px solid #d1d5db;
}
.results-table {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.79rem;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
.results-table th {
    padding: 9px 11px;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    white-space: nowrap;
    text-align: right;
}
.results-table th:first-child { text-align: left; }
.results-table td {
    padding: 8px 11px;
    text-align: right;
    border-bottom: 1px solid #f0f2f5;
    white-space: nowrap;
}
.results-table td:first-child { text-align: left; font-weight: 500; }
.results-table tbody tr:hover td { background: #f5f9ff !important; }

/* Instrument card number badge */
.inst-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px; height: 22px;
    background: #1a4fa8;
    color: white;
    border-radius: 50%;
    font-size: 0.7rem;
    font-weight: 700;
    margin-right: 6px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════
def fmt_ars(n, dec=2):
    """Formato argentino: . miles, , decimal"""
    if n is None or (isinstance(n, float) and (math.isnan(n) or math.isinf(n))):
        return "—"
    s = f"{abs(n):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if n < 0 else "") + s

def numero_a_palabras(n):
    """Número entero a palabras en español"""
    if n is None or (isinstance(n, float) and (math.isnan(n) or math.isinf(n))):
        return ""
    ni = int(abs(n))
    if ni == 0:
        return "cero"

    ONES = ["","uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve",
            "diez","once","doce","trece","catorce","quince","dieciséis","diecisiete",
            "dieciocho","diecinueve","veinte"]
    TENS  = ["","","veinte","treinta","cuarenta","cincuenta","sesenta","setenta","ochenta","noventa"]
    HUNDS = ["","ciento","doscientos","trescientos","cuatrocientos","quinientos",
             "seiscientos","setecientos","ochocientos","novecientos"]

    def lt100(x):
        if x <= 20: return ONES[x]
        d, u = divmod(x, 10)
        if d == 2 and u: return "veinti" + ONES[u]
        return TENS[d] + (" y " + ONES[u] if u else "")

    def lt1000(x):
        if x == 0:   return ""
        if x == 100: return "cien"
        if x < 100:  return lt100(x)
        c, r = divmod(x, 100)
        return HUNDS[c] + (" " + lt100(r) if r else "")

    parts, rem = [], ni
    if rem >= 1_000_000:
        m, rem = divmod(rem, 1_000_000)
        parts.append("un millón" if m == 1 else lt1000(m) + " millones")
    if rem >= 1_000:
        k, rem = divmod(rem, 1_000)
        parts.append("mil" if k == 1 else lt1000(k) + " mil")
    if rem:
        parts.append(lt1000(rem))
    return " ".join(parts)

def words_html(val, suffix=""):
    w = numero_a_palabras(val)
    if not w:
        return ""
    return f'<div class="words-hint">{w}{suffix}</div>'

# ══════════════════════════════════════════════════
# FÓRMULAS (replicadas del Excel exactamente)
# ══════════════════════════════════════════════════
def get_dias(fl, fp):
    if not fl or not fp:
        return 0
    try:
        return (fp - fl).days
    except Exception:
        return 0

def calc_row(fl, fp, vn_usd, tc, tna_pct, p, garantizado):
    """
    fl, fp   = date objects
    vn_usd   = Valor Nominal en USD  (F)
    tc       = Tipo de Cambio        (G)
    tna_pct  = TNA en %              (I)
    p        = dict de parámetros
    """
    dias = get_dias(fl, fp)
    tna  = tna_pct / 100.0

    H = vn_usd * tc                                                     # Valor Nominal Pesos
    denom = 1 + tna * dias / 365
    J = H / denom if dias > 0 and denom != 0 else H                    # Importe Bruto
    K = H - J                                                            # Descuento

    # L — Derechos de Mercado: IF(E<>0, IF(E>90, J*E7, J*E7/90*E), 0)
    if dias != 0:
        L = (J * p["der"] if dias > 90 else J * p["der"] / 90 * dias)
    else:
        L = 0.0

    # M — Arancel Rosental: IF(H<>0, IF((H*G10/365*E)<G9, G9, H*G10/365*E), 0)
    if H != 0:
        ar_base = H * p["com"] / 365 * dias
        M = p["boleto"] if ar_base < p["boleto"] else ar_base
    else:
        M = 0.0

    N = (L + M) * 0.21                                                  # IVA Gastos
    O = L + M + N                                                        # Total Gastos
    P_col = H - K - O                                                    # Total Boleto = J - O

    # SGR: Q = H*0.02*(E-2)/365 ; R = H*0.002*1.21
    Q = H * p["sgr_com"] * (dias - 2) / 365
    R = H * p["sgr_caja"] * 1.21
    S = Q + R

    # T = H - K - O - S  (sin SGR → S=0)
    T = H - K - O - (S if garantizado else 0)

    return dict(dias=dias, H=H, J=J, K=K, L=L, M=M, N=N, O=O, P=P_col, Q=Q, R=R, S=S, T=T)

# ══════════════════════════════════════════════════
# HTML TABLE
# ══════════════════════════════════════════════════
def build_table(rows, garantizado):
    G  = "#f1f3f6"   # grey cell
    GB = "#e8edf2"   # grey header
    BL = "#dbeafe"   # blue highlight
    YL = "#fef3c7"   # yellow SGR
    GN = "#dcfce7"   # green neto
    TK = "#1e293b"   # totals background

    sgr = "" if garantizado else "display:none;"

    TH = (f"padding:9px 10px;font-size:0.66rem;font-weight:700;"
          f"text-transform:uppercase;letter-spacing:.4px;white-space:nowrap;text-align:right;")

    def th(txt, bg, extra="", rowspan="", colspan=""):
        rs = f' rowspan="{rowspan}"' if rowspan else ""
        cs = f' colspan="{colspan}"' if colspan else ""
        return f'<th{rs}{cs} style="{TH}background:{bg};{extra}">{txt}</th>'

    def td(val, bg="white", extra=""):
        v = fmt_ars(val) if isinstance(val, (int, float)) else str(val)
        return f'<td style="padding:8px 10px;text-align:right;background:{bg};{extra}">{v}</td>'

    def td_l(val, extra=""):
        return f'<td style="padding:8px 10px;text-align:left;font-weight:500;{extra}">{val}</td>'

    # ── HEADER ──────────────────────────────────────
    thead = f"""
    <thead>
      <tr>
        {th("Instrumento",  GB, "text-align:left;min-width:130px;", rowspan=2)}
        {th("Días",         GB, "", rowspan=2)}
        {th("Valores",      GB, "text-align:center;border-left:2px solid #cbd5e1;", colspan=3)}
        {th("Gastos Mercado y Arancel", GB, "text-align:center;border-left:2px solid #cbd5e1;", colspan=4)}
        {th("Total<br>Boleto", BL, "border-left:2px solid #60a5fa;color:#1d40af;min-width:110px;", rowspan=2)}
        {th("SGR", YL, f"text-align:center;border-left:2px solid #d97706;{sgr}", colspan=3)}
        {th("NETO A<br>COBRAR", GN, "border-left:2px solid #34d399;color:#065f46;min-width:110px;", rowspan=2)}
      </tr>
      <tr>
        {th("VN Pesos",       GB, "border-left:2px solid #cbd5e1;")}
        {th("Importe Bruto",  GB)}
        {th("Descuento",      GB)}
        {th("Der. Mercado",   GB, "border-left:2px solid #cbd5e1;")}
        {th("Arancel",        GB)}
        {th("IVA Gastos",     GB)}
        {th("Total Gastos",   GB)}
        {th("Com. SGR",       YL, f"border-left:2px solid #d97706;{sgr}")}
        {th("Caja Val.",      YL, sgr)}
        {th("Total SGR",      YL, sgr)}
      </tr>
    </thead>"""

    # ── ROWS ────────────────────────────────────────
    tbody = "<tbody>"
    totals = {k: 0.0 for k in ["H","J","K","L","M","N","O","P","Q","R","S","T"]}

    for row in rows:
        c = row["calc"]
        nombre = row["nombre"]
        for k in totals:
            totals[k] += c[k]

        tbody += f"""
        <tr>
          {td_l(nombre)}
          <td style="padding:8px 10px;text-align:right;background:{G};">{int(c['dias'])}</td>
          {td(c['H'],  G,  "border-left:2px solid #d1d5db;")}
          {td(c['J'],  G)}
          {td(c['K'],  G)}
          {td(c['L'],  G,  "border-left:2px solid #d1d5db;")}
          {td(c['M'],  G)}
          {td(c['N'],  G)}
          {td(c['O'],  G)}
          {td(c['P'],  BL, "font-weight:600;border-left:2px solid #93c5fd;")}
          <td style="padding:8px 10px;text-align:right;background:{YL};border-left:2px solid #fcd34d;{sgr}">{fmt_ars(c['Q'])}</td>
          <td style="padding:8px 10px;text-align:right;background:{YL};{sgr}">{fmt_ars(c['R'])}</td>
          <td style="padding:8px 10px;text-align:right;background:{YL};{sgr}">{fmt_ars(c['S'])}</td>
          {td(c['T'],  GN, "font-weight:700;color:#065f46;border-left:2px solid #6ee7b7;")}
        </tr>"""

    # ── TOTALS ROW ──────────────────────────────────
    TS = f"padding:12px 10px;text-align:right;background:{TK};color:#f8fafc;font-weight:700;font-size:0.83rem;"
    tbody += f"""
        <tr>
          <td style="{TS}text-align:left;font-size:0.88rem;letter-spacing:.3px;">▶ TOTALES</td>
          <td style="{TS}">—</td>
          <td style="{TS}border-left:2px solid #374151;">{fmt_ars(totals['H'])}</td>
          <td style="{TS}">{fmt_ars(totals['J'])}</td>
          <td style="{TS}">{fmt_ars(totals['K'])}</td>
          <td style="{TS}border-left:2px solid #374151;">{fmt_ars(totals['L'])}</td>
          <td style="{TS}">{fmt_ars(totals['M'])}</td>
          <td style="{TS}">{fmt_ars(totals['N'])}</td>
          <td style="{TS}">{fmt_ars(totals['O'])}</td>
          <td style="{TS}color:#93c5fd;border-left:2px solid #374151;">{fmt_ars(totals['P'])}</td>
          <td style="{TS}color:#fcd34d;border-left:2px solid #374151;{sgr}">{fmt_ars(totals['Q'])}</td>
          <td style="{TS}color:#fcd34d;{sgr}">{fmt_ars(totals['R'])}</td>
          <td style="{TS}color:#fcd34d;{sgr}">{fmt_ars(totals['S'])}</td>
          <td style="{TS}color:#86efac;font-size:0.92rem;border-left:2px solid #374151;">{fmt_ars(totals['T'])}</td>
        </tr>"""

    tbody += "</tbody>"
    return f'<div class="results-table-wrapper"><table class="results-table">{thead}{tbody}</table></div>'

# ══════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════
def init():
    defaults = {
        "instrument_ids": [],
        "next_id": 1,
        "garantizado": True,
        # Params (stored as displayed % where applicable)
        "p_der":    0.0600,   # 0.06%  → rate = /100
        "p_com":    1.5000,   # 1.5%   → rate = /100
        "p_boleto": 100.00,   # $100
        "p_sgr_com":  2.0000, # 2%     → rate = /100
        "p_sgr_caja": 0.2000, # 0.2%   → rate = /100
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

def get_params():
    return {
        "der":      st.session_state.p_der    / 100,
        "com":      st.session_state.p_com    / 100,
        "boleto":   st.session_state.p_boleto,
        "sgr_com":  st.session_state.p_sgr_com  / 100,
        "sgr_caja": st.session_state.p_sgr_caja / 100,
    }

def add_instrument():
    iid = st.session_state.next_id
    st.session_state.next_id += 1
    n = len(st.session_state.instrument_ids) + 1
    st.session_state.instrument_ids.append(iid)
    st.session_state[f"n_{iid}"]   = f"Instrumento {n}"
    st.session_state[f"fl_{iid}"]  = date.today()
    st.session_state[f"fp_{iid}"]  = date.today()
    st.session_state[f"vn_{iid}"]  = 0.0
    st.session_state[f"tc_{iid}"]  = 0.0
    st.session_state[f"tna_{iid}"] = 0.0

def delete_instrument(iid):
    st.session_state.instrument_ids = [x for x in st.session_state.instrument_ids if x != iid]
    for k in [f"n_{iid}", f"fl_{iid}", f"fp_{iid}", f"vn_{iid}", f"tc_{iid}", f"tna_{iid}"]:
        st.session_state.pop(k, None)

def clear_all():
    for iid in st.session_state.instrument_ids.copy():
        for k in [f"n_{iid}", f"fl_{iid}", f"fp_{iid}", f"vn_{iid}", f"tc_{iid}", f"tna_{iid}"]:
            st.session_state.pop(k, None)
    st.session_state.instrument_ids = []
    st.session_state.next_id = 1

# ══════════════════════════════════════════════════
# ── HEADER ──
# ══════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
  <div>
    <h1>📄 Operatoria de Compra de Pagaré</h1>
    <p>Rosental S.A. Sociedad de Bolsa — Pagaré en Dólares</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# ── GARANTIZADO TOGGLE ──
# ══════════════════════════════════════════════════
col_tog, col_info = st.columns([2, 5])
with col_tog:
    grt_opts = ["✅ Garantizado", "🔓 No Garantizado"]
    sel = st.radio(
        "**Tipo de instrumento**",
        grt_opts,
        horizontal=True,
        index=0 if st.session_state.garantizado else 1,
        key="_grt_radio",
    )
    st.session_state.garantizado = sel == grt_opts[0]
garantizado = st.session_state.garantizado

# ══════════════════════════════════════════════════
# ── PARAMETERS ──
# ══════════════════════════════════════════════════
with st.expander("⚙️  Gastos y Aranceles — Parámetros", expanded=True):
    n_cols = 4 if garantizado else 2
    cols = st.columns(n_cols)

    with cols[0]:
        st.markdown('<div class="param-card"><h4>📊 Derechos de Mercado</h4>', unsafe_allow_html=True)
        st.number_input(
            "Tasa anual + IVA (%)", min_value=0.0, step=0.01,
            format="%.4f", key="p_der",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with cols[1]:
        st.markdown('<div class="param-card"><h4>🏢 Arancel Rosental S.A.</h4>', unsafe_allow_html=True)
        st.number_input("Comisión anual + IVA (%)", min_value=0.0, step=0.1, format="%.4f", key="p_com")
        st.number_input("Boleto Mínimo ($)",        min_value=0.0, step=10.0, format="%.2f", key="p_boleto")
        st.markdown("</div>", unsafe_allow_html=True)

    if garantizado:
        with cols[2]:
            st.markdown('<div class="param-card"><h4>🔒 SGR — Comisión</h4>', unsafe_allow_html=True)
            st.number_input("Tasa anual (%)", min_value=0.0, step=0.1, format="%.4f", key="p_sgr_com")
            st.markdown("</div>", unsafe_allow_html=True)

        with cols[3]:
            st.markdown('<div class="param-card"><h4>🏦 SGR — Caja de Valores</h4>', unsafe_allow_html=True)
            st.number_input("Tasa × 1,21 IVA (%)", min_value=0.0, step=0.01, format="%.4f", key="p_sgr_caja")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:0.72rem;color:#9ca3af;margin-top:8px;'>"
        "(*) Tipo de cambio estimado. TC Com. BNA billete vendedor</p>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════
# ── INSTRUMENTS ──
# ══════════════════════════════════════════════════
st.markdown("---")
col_add, col_count, col_del = st.columns([2, 4, 2])
with col_add:
    if st.button("➕  Agregar Instrumento", use_container_width=True, type="primary"):
        add_instrument()
        st.rerun()

with col_count:
    n_inst = len(st.session_state.instrument_ids)
    if n_inst > 0:
        st.markdown(
            f"<p style='color:#6b7280;font-size:0.85rem;padding-top:8px;'>"
            f"<b>{n_inst}</b> instrumento{'s' if n_inst > 1 else ''}</p>",
            unsafe_allow_html=True,
        )

with col_del:
    if n_inst > 0:
        if st.button("🗑  Borrar Todo", use_container_width=True):
            clear_all()
            st.rerun()

# Render each instrument card
for idx, iid in enumerate(st.session_state.instrument_ids):

    with st.container(border=True):
        # Card header row
        hcol1, hcol2 = st.columns([8, 1])
        with hcol1:
            st.markdown(
                f'<span class="inst-badge">{idx + 1}</span>'
                f'<b style="color:#0f4c81;font-size:0.9rem;">Instrumento {idx + 1}</b>',
                unsafe_allow_html=True,
            )
            st.text_input(
                "Nombre del instrumento",
                key=f"n_{iid}",
                label_visibility="collapsed",
                placeholder="Nombre del instrumento…",
            )
        with hcol2:
            st.write("")
            if st.button("✕", key=f"del_{iid}", help="Borrar instrumento"):
                delete_instrument(iid)
                st.rerun()

        # Inputs row
        c1, c2, c3, c4, c5 = st.columns([1.6, 1.6, 2, 1.6, 1])

        with c1:
            st.markdown('<div class="section-label">📅 Fecha Liquidación</div>', unsafe_allow_html=True)
            st.date_input("Fecha Liquidación", key=f"fl_{iid}", label_visibility="collapsed")

        with c2:
            st.markdown('<div class="section-label">📅 Fecha de Pago</div>', unsafe_allow_html=True)
            st.date_input("Fecha de Pago", key=f"fp_{iid}", label_visibility="collapsed")

        with c3:
            st.markdown('<div class="section-label">💵 Valor Nominal (USD)</div>', unsafe_allow_html=True)
            vn_val = st.number_input(
                "VN USD", min_value=0.0, step=1000.0, format="%.2f",
                key=f"vn_{iid}", label_visibility="collapsed",
            )
            st.markdown(
                f'<div class="words-hint">'
                f'<b>{fmt_ars(vn_val)}</b> &nbsp;·&nbsp; '
                f'<i>{numero_a_palabras(vn_val)}</i>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c4:
            st.markdown('<div class="section-label">🔄 Tipo de Cambio</div>', unsafe_allow_html=True)
            tc_val = st.number_input(
                "TC", min_value=0.0, step=10.0, format="%.2f",
                key=f"tc_{iid}", label_visibility="collapsed",
            )
            st.markdown(
                f'<div class="words-hint">'
                f'<b>{fmt_ars(tc_val)}</b> &nbsp;·&nbsp; '
                f'<i>{numero_a_palabras(tc_val)}</i>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c5:
            st.markdown('<div class="section-label">📈 TNA (%)</div>', unsafe_allow_html=True)
            tna_val = st.number_input(
                "TNA", min_value=0.0, max_value=9999.0, step=0.5, format="%.2f",
                key=f"tna_{iid}", label_visibility="collapsed",
            )
            st.markdown(
                f'<div class="words-hint">'
                f'<i>{numero_a_palabras(tna_val)} %</i>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════
# ── RESULTS TABLE ──
# ══════════════════════════════════════════════════
if st.session_state.instrument_ids:
    st.markdown("---")
    st.markdown("### 📊 Resultados — Tabla de Cálculo")

    params = get_params()
    rows_data = []

    for iid in st.session_state.instrument_ids:
        vn  = st.session_state.get(f"vn_{iid}",  0.0)
        tc  = st.session_state.get(f"tc_{iid}",  0.0)
        tna = st.session_state.get(f"tna_{iid}", 0.0)
        fl  = st.session_state.get(f"fl_{iid}",  date.today())
        fp  = st.session_state.get(f"fp_{iid}",  date.today())
        nm  = st.session_state.get(f"n_{iid}",   f"Instrumento {iid}")

        calc = calc_row(fl, fp, vn, tc, tna, params, garantizado)
        rows_data.append({"nombre": nm, "calc": calc})

    html_table = build_table(rows_data, garantizado)
    st.markdown(html_table, unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:0.72rem;color:#9ca3af;margin-top:10px;'>"
        "(*) Tipo de cambio estimado. TC Com. BNA billete vendedor</p>",
        unsafe_allow_html=True,
    )
