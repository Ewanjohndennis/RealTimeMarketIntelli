import io
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# 1.  TEXT CLEANING  (the root cause of the black boxes)
# ─────────────────────────────────────────────────────────────────────────────

# Characters ReportLab's built-in fonts cannot render → replace with ASCII
_UNICODE_REPLACEMENTS = [
    ("■", "-"),          # BLACK SQUARE  ← main culprit in your PDF
    ("●", "-"),          # BLACK CIRCLE
    ("•",  "-"),         # BULLET
    ("→", "->"),
    ("←", "<-"),
    ("–", "-"),          # EN DASH
    ("—", "--"),         # EM DASH
    ("\u2019", "'"),     # RIGHT SINGLE QUOTATION MARK
    ("\u2018", "'"),     # LEFT SINGLE QUOTATION MARK
    ("\u201c", '"'),     # LEFT DOUBLE QUOTATION MARK
    ("\u201d", '"'),     # RIGHT DOUBLE QUOTATION MARK
    ("\u2022", "-"),     # BULLET (another encoding)
    ("\u00ae", "(R)"),   # REGISTERED SIGN
    ("\u00a9", "(C)"),   # COPYRIGHT SIGN
    ("\u2026", "..."),   # HORIZONTAL ELLIPSIS
    ("\xa0", " "),       # NON-BREAKING SPACE
]

# ReportLab uses XML-like markup in Paragraph — must escape bare & < >
def _escape_xml(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def clean_ai_text(text: str) -> str:
    """
    Sanitise LLM output so it renders cleanly in ReportLab Paragraphs.
    Call this on every string before passing to add_section() or Paragraph().
    """
    if not text:
        return ""

    text = str(text)

    # ── 1. Fix unicode characters that cause black boxes ──────────────────────
    for bad, good in _UNICODE_REPLACEMENTS:
        text = text.replace(bad, good)

    # Fix (cid:N) — appears when pdfplumber extracts ■ and other unencoded symbols
    text = re.sub(r"\(cid:\d+\)", "-", text)

    # ── 2. Strip markdown formatting ──────────────────────────────────────────
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)   # **bold** / *italic*
    text = re.sub(r"#{1,6}\s*", "", text)                  # ### headings
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)      # `code`

    # ── 3. Remove markdown table rows (lines starting/ending with |) ──────────
    # Also removes lines that are ONLY pipes and dashes (separator rows)
    text = re.sub(r"^\s*\|.*\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-|: ]+\s*$", "", text, flags=re.MULTILINE)

    # ── 4. Remove any remaining stray pipes ──────────────────────────────────
    text = re.sub(r"\|", "", text)

    # ── 5. Fix ReportLab line-break tag ──────────────────────────────────────
    text = text.replace("<br>", "<br/>")

    # ── 6. Collapse excessive blank lines ────────────────────────────────────
    text = re.sub(r"\n{3,}", "\n\n", text)

    # ── 7. Escape XML special chars LAST (after all regex work) ──────────────
    text = _escape_xml(text)

    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# 2.  PDF GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def _make_styles():
    base = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=base["Title"],
        fontSize=22,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=base["Heading1"],
        fontSize=14,
        spaceAfter=4,
        spaceBefore=12,
        textColor=colors.HexColor("#185FA5"),
    )
    body_style = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=10,
        spaceAfter=5,
        leading=15,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=base["Normal"],
        fontSize=10,
        spaceAfter=4,
        leading=15,
        leftIndent=16,
        firstLineIndent=-12,    # hanging indent so bullet aligns nicely
    )
    caption_style = ParagraphStyle(
        "Caption",
        parent=base["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        spaceAfter=12,
    )
    return title_style, h1_style, body_style, bullet_style, caption_style


def _add_section(story, title, content, h1_style, body_style, bullet_style):
    """Render a titled section. Lines starting with '-' become bullet points."""
    story.append(Paragraph(title, h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#185FA5")))
    story.append(Spacer(1, 6))

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Detect bullet lines: start with  -  or  •  after cleaning
        if re.match(r"^[-\-]\s+", line):
            bullet_text = re.sub(r"^[-\-]\s+", "", line)
            story.append(Paragraph(f"- {bullet_text}", bullet_style))
        else:
            story.append(Paragraph(line, body_style))

    story.append(Spacer(1, 10))


def generate_pdf(company, competitors, brief, news_out, comp_out,
                 fin_out, improve_out, financials, ticker_map,
                 generated_at) -> bytes:
    """
    Build and return the intelligence report as PDF bytes.
    Drop-in replacement for your original generate_pdf().
    """
    # ── Clean all LLM text ────────────────────────────────────────────────────
    brief      = clean_ai_text(brief)
    news_out   = clean_ai_text(news_out)
    comp_out   = clean_ai_text(comp_out)
    fin_out    = clean_ai_text(fin_out)
    improve_out = clean_ai_text(improve_out)
    company_display = _escape_xml(str(company))

    financials = financials or {}
    ticker_map = ticker_map or {}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    title_style, h1_style, body_style, bullet_style, caption_style = _make_styles()
    base_styles = getSampleStyleSheet()
    story = []

    # ── Cover ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(company_display, title_style))
    story.append(Paragraph("Intelligence Report", base_styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Generated: {_escape_xml(str(generated_at))}", caption_style))

    if competitors:
        benchmarked = _escape_xml(", ".join(competitors))
        story.append(Paragraph(f"Benchmarked against: {benchmarked}", caption_style))

    story.append(HRFlowable(width="100%", thickness=1,
                            color=colors.HexColor("#185FA5")))
    story.append(Spacer(1, 0.2 * inch))

    _add_section(story, "Executive Brief", brief,
                 h1_style, body_style, bullet_style)
    story.append(PageBreak())

    # ── Financial Metrics Table ───────────────────────────────────────────────
    story.append(Paragraph("Financial Metrics", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#185FA5")))
    story.append(Spacer(1, 8))

    pdf_metrics = [
        ("Current Price",    "current_price",    lambda v: f"${v:.2f}"),
        ("Market Cap",       "market_cap",        lambda v: f"${v/1e9:.1f}B"),
        ("TTM Revenue",      "revenue_ttm",       lambda v: f"${v/1e9:.1f}B"),
        ("Gross Margin",     "gross_margin",      lambda v: f"{v*100:.1f}%"),
        ("Operating Margin", "operating_margin",  lambda v: f"{v*100:.1f}%"),
        ("P/E Ratio",        "pe_ratio",          lambda v: f"{v:.1f}x"),
        ("EPS",              "eps",               lambda v: f"${v:.2f}"),
        ("Return on Equity", "return_on_equity",  lambda v: f"{v*100:.1f}%"),
        ("52W High",         "52w_high",          lambda v: f"${float(v):.2f}"),
        ("52W Low",          "52w_low",           lambda v: f"${float(v):.2f}"),
    ]

    company_list = list(ticker_map.keys())
    table_data = [["Metric"] + company_list]

    for label, key, fmt in pdf_metrics:
        row = [label]
        for comp in company_list:
            ticker = ticker_map.get(comp, "")
            fin    = financials.get(ticker, {})
            val    = fin.get(key, None)
            try:
                row.append(fmt(val) if val is not None else "N/A")
            except Exception:
                row.append("N/A")
        table_data.append(row)

    col_count = len(table_data[0])
    col_width = (6.5 * inch) / col_count

    tbl = Table(table_data, colWidths=[col_width] * col_count)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#185FA5")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1),
         [colors.HexColor("#f5f8ff"), colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("ROWHEIGHT",     (0, 0), (-1, -1), 18),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 16))
    story.append(PageBreak())

    # ── Analysis Sections ─────────────────────────────────────────────────────
    _add_section(story, "News & Sentiment Analysis", news_out,
                 h1_style, body_style, bullet_style)
    _add_section(story, "Competitor Analysis", comp_out,
                 h1_style, body_style, bullet_style)
    _add_section(story, "Financial Analysis", fin_out,
                 h1_style, body_style, bullet_style)
    story.append(PageBreak())

    _add_section(story, "Strategic Recommendations", improve_out,
                 h1_style, body_style, bullet_style)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#cccccc")))
    story.append(Paragraph(
        "Auto-generated by Company Intelligence Dashboard. "
        "Data sourced from Google News RSS, SerpAPI, and Yahoo Finance.",
        caption_style,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ─────────────────────────────────────────────────────────────────────────────
# 3.  REPORT UPLOAD HANDLER  (McKinsey / Gartner / any industry PDF)
# ─────────────────────────────────────────────────────────────────────────────

def extract_report_text(uploaded_file) -> dict:
    """
    Extract and clean text from an uploaded industry report PDF.
    Works with Streamlit's UploadedFile or any file-like object.

    Returns
    -------
    {
        "full_text"   : str   – complete cleaned text
        "pages"       : int   – page count
        "preview"     : str   – first 500 chars for display
        "ticker_hint" : str   – any stock tickers detected in the text
        "topic_hint"  : str   – first 10 meaningful words (for RSS topic)
    }
    """
    import pdfplumber

    raw_text = ""
    page_count = 0

    with pdfplumber.open(uploaded_file) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"

    # Clean the extracted text same way we clean LLM output
    cleaned = clean_ai_text(raw_text)

    # Try to detect stock tickers (1-5 uppercase letters standalone)
    tickers_found = list(set(re.findall(r"\b([A-Z]{1,5})\b", raw_text)))
    # Filter out common English words that look like tickers
    _noise = {"A", "I", "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU",
              "ALL", "CAN", "HER", "WAS", "ONE", "OUR", "OUT", "DAY",
              "GET", "HAS", "HIM", "HIS", "HOW", "ITS", "MAY", "NEW",
              "NOW", "OLD", "SEE", "TWO", "WAY", "WHO", "BOY", "DID",
              "USE", "CEO", "CFO", "COO", "CTO", "IPO", "GDP", "ROI",
              "US", "UK", "EU", "AI", "ML", "IT"}
    tickers_found = [t for t in tickers_found if t not in _noise][:5]

    # Build a topic hint from first meaningful words
    words = [w for w in cleaned.split() if len(w) > 4][:10]
    topic_hint = " ".join(words)

    return {
        "full_text"  : cleaned,
        "pages"      : page_count,
        "preview"    : cleaned[:500] + ("..." if len(cleaned) > 500 else ""),
        "ticker_hint": ", ".join(tickers_found),
        "topic_hint" : topic_hint,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4.  STREAMLIT UPLOAD + FORECAST WIDGET
#     Paste this block into your Streamlit dashboard page
# ─────────────────────────────────────────────────────────────────────────────

def render_report_upload_section(default_ticker="", default_topic=""):
    """
    Complete Streamlit UI block for uploading an industry report PDF
    and running LSTM forecasting on it.

    Usage in your app.py / dashboard:
        from pdf_generator import render_report_upload_section
        render_report_upload_section()
    """

    st.subheader("📄 Upload Industry Report for Forecasting")
    st.caption(
        "Upload a McKinsey, Gartner, or any PDF market report. "
        "The system will extract the text and use it to guide the LSTM forecasting."
    )

    uploaded = st.file_uploader(
        "Choose a PDF report",
        type=["pdf"],
        help="Max 50MB. Works with McKinsey, Gartner, Bloomberg, Deloitte reports."
    )

    if not uploaded:
        return

    with st.spinner("Reading report..."):
        report_data = extract_report_text(uploaded)

    st.success(f"Report loaded — {report_data['pages']} pages extracted.")

    with st.expander("Preview extracted text"):
        st.text(report_data["preview"])

    st.divider()

    # ── Let user confirm / override the auto-detected inputs ─────────────────
    col1, col2 = st.columns(2)

    with col1:
     ticker = st.text_input(
        "Stock ticker to forecast",
        value=default_ticker or report_data["ticker_hint"].split(",")[0].strip(),
        help="E.g. AAPL, MSFT, NVDA"
    )

    with col2:
        topic = st.text_input(
        "Industry topic (for news RSS)",
        value=default_topic or report_data["topic_hint"][:60],
        help="Used to pull relevant Google News headlines"
    )

    forecast_days = st.slider("Forecast horizon (days)", 7, 90, 30)

    if st.button("Run Forecast from Report", type="primary"):

        # Import here to avoid circular imports in your project
        from agents.forecasting_agent import ForecastingAgent, render_streamlit

        if not ticker:
            st.error("Please enter a stock ticker.")
            return

        with st.spinner(f"Training LSTM models for {ticker}..."):
            agent = ForecastingAgent(
                ticker=ticker.strip().upper(),
                topic=topic.strip(),
                history_days=180,
            )
            results = agent.run(forecast_days=forecast_days)

        st.success("Forecasting complete!")

        # Show the report context that was used
        with st.expander("Report context used for topic extraction"):
            st.info(
                f"**Detected tickers:** {report_data['ticker_hint'] or 'None'}\n\n"
                f"**Topic used for RSS:** {topic}\n\n"
                f"**Pages processed:** {report_data['pages']}"
            )

        # Render all three forecast charts
        render_streamlit(results)