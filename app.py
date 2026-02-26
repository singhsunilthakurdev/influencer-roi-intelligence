import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Influencer ROI Intelligence", layout="wide")

# ---------------------------------------------------
# PREMIUM DASHBOARD STYLING
# ---------------------------------------------------
st.markdown("""
<style>
.metric-card {
    background-color: #111111;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #222;
}
.big-number {
    font-size: 26px;
    font-weight: bold;
}
.section-title {
    font-size: 22px;
    margin-top: 30px;
    margin-bottom: 10px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.title("Influencer ROI Intelligence Dashboard")

brand_name = st.text_input("Brand Name")

orders_file = st.file_uploader("Upload Shopify Orders CSV", type=["csv"])
mapping_file = st.file_uploader("Upload Coupon Mapping CSV", type=["csv"])

margin_percent = st.number_input("Estimated Margin %", min_value=0, max_value=100)

def performance_icon(roi):
    if roi > 50:
        return "🟢"
    elif roi >= 0:
        return "🟡"
    else:
        return "🔴"

# ---------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------
if orders_file and mapping_file and margin_percent > 0:

    orders_df = pd.read_csv(orders_file)
    mapping_df = pd.read_csv(mapping_file)

    margin = margin_percent / 100

    # ---------- Coupon Summary ----------
    summary = (
        orders_df.groupby("Discount Code")["Total"]
        .agg(["count", "sum"])
        .reset_index()
    )
    summary.columns = ["Coupon Code", "Orders", "Revenue"]
    summary["Gross Profit"] = summary["Revenue"] * margin

    final_df = pd.merge(summary, mapping_df, on="Coupon Code", how="left")
    final_df["Fee"] = final_df["Fee"].fillna(0)

    final_df["Net Profit"] = final_df["Gross Profit"] - final_df["Fee"]

    final_df["ROI %"] = final_df.apply(
        lambda row: (row["Net Profit"] / row["Fee"] * 100)
        if row["Fee"] > 0 else 0,
        axis=1
    )

    final_df["Performance"] = final_df["ROI %"].apply(performance_icon)
    final_df = final_df.round(2)

    # ---------- Influencer Summary ----------
    influencer_summary = (
        final_df.groupby("Influencer Name")
        .agg({
            "Revenue": "sum",
            "Gross Profit": "sum",
            "Fee": "sum",
            "Net Profit": "sum"
        })
        .reset_index()
    )

    influencer_summary["ROI %"] = influencer_summary.apply(
        lambda row: (row["Net Profit"] / row["Fee"] * 100)
        if row["Fee"] > 0 else 0,
        axis=1
    )

    influencer_summary["Performance"] = influencer_summary["ROI %"].apply(performance_icon)
    influencer_summary = influencer_summary.round(2)

    total_revenue = influencer_summary["Revenue"].sum()
    total_fee = influencer_summary["Fee"].sum()
    total_profit = influencer_summary["Net Profit"].sum()
    total_roi = (total_profit / total_fee * 100) if total_fee > 0 else 0

    # ---------------------------------------------------
    # METRIC CARDS
    # ---------------------------------------------------
    st.markdown("<div class='section-title'>Campaign Overview</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"""
    <div class='metric-card'>
        <div>Total Revenue</div>
        <div class='big-number'>${total_revenue:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div class='metric-card'>
        <div>Total Fees</div>
        <div class='big-number'>${total_fee:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div class='metric-card'>
        <div>Net Profit</div>
        <div class='big-number'>${total_profit:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    col4.markdown(f"""
    <div class='metric-card'>
        <div>Overall ROI</div>
        <div class='big-number'>{total_roi:.1f}% {performance_icon(total_roi)}</div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------
    # TABLES
    # ---------------------------------------------------
    st.markdown("<div class='section-title'>Influencer Performance</div>", unsafe_allow_html=True)
    st.dataframe(influencer_summary.sort_values("ROI %", ascending=False))

    st.markdown("<div class='section-title'>Coupon Breakdown</div>", unsafe_allow_html=True)
    st.dataframe(final_df.sort_values("ROI %", ascending=False))

    # Underperformers
    weak = influencer_summary[influencer_summary["ROI %"] < 0]
    if not weak.empty:
        st.markdown("<div class='section-title'>⚠ Underperforming Influencers</div>", unsafe_allow_html=True)
        st.dataframe(weak)

    # ---------------------------------------------------
    # DASHBOARD FOOTER
    # ---------------------------------------------------
    st.markdown("---")
    st.markdown(f"""
    **Brand:** {brand_name}  
    **Generated:** {datetime.now().strftime('%d %B %Y')}  
    **Audited by Global Technology Ventures LLC**
    """)

    # ---------------------------------------------------
    # CONSULTING PDF
    # ---------------------------------------------------
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Influencer ROI Executive Intelligence Report", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Prepared For: {brand_name}", styles['Heading2']))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%d %B %Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Executive Summary", styles['Heading2']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Total Revenue: ${total_revenue:,.2f}", styles['Normal']))
    elements.append(Paragraph(f"Total Investment: ${total_fee:,.2f}", styles['Normal']))
    elements.append(Paragraph(f"Net Profit: ${total_profit:,.2f}", styles['Normal']))
    elements.append(Paragraph(f"Overall ROI: {total_roi:.2f}%", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Chart
    if not influencer_summary.empty:
        plt.figure(figsize=(6,3))
        plt.bar(influencer_summary["Influencer Name"], influencer_summary["ROI %"])
        plt.title("ROI % by Influencer")
        plt.tight_layout()

        chart_buffer = BytesIO()
        plt.savefig(chart_buffer, format="png")
        plt.close()
        chart_buffer.seek(0)

        elements.append(Paragraph("ROI Visualization", styles['Heading2']))
        elements.append(Spacer(1, 10))
        elements.append(Image(chart_buffer, width=400, height=200))
        elements.append(Spacer(1, 20))

    # Influencer Table
    pdf_table_data = [influencer_summary.columns.tolist()] + influencer_summary.values.tolist()
    table = Table(pdf_table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.black),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 40))

    # Signature Block
    elements.append(Paragraph("Prepared & Audited By:", styles['Normal']))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("Global Technology Ventures LLC", styles['Heading3']))
    elements.append(Paragraph("Strategic Revenue Intelligence Division", styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Authorized Signature:", styles['Normal']))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("______________________________", styles['Normal']))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("Managing Director", styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Confidential – Internal Strategic Document", styles['Normal']))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    st.download_button(
        "Download Executive Consulting Report (PDF)",
        data=pdf,
        file_name=f"{brand_name}_Executive_ROI_Report.pdf",
        mime="application/pdf"
    )