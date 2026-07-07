from __future__ import annotations

import logging

import pandas as pd

from src.utils import project_path


def _write_table(writer: pd.ExcelWriter, sheet_name: str, dataframe: pd.DataFrame, title: str) -> None:
    workbook = writer.book
    title_format = workbook.add_format({"bold": True, "font_size": 15, "font_color": "#1F4E78"})
    note_format = workbook.add_format({"italic": True, "font_color": "#666666"})
    header_format = workbook.add_format({"bold": True, "bg_color": "#D9EAF7", "border": 1})
    currency_format = workbook.add_format({"num_format": "$#,##0.00"})
    integer_format = workbook.add_format({"num_format": "#,##0"})
    percent_format = workbook.add_format({"num_format": "0.0%"})
    date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})

    dataframe.to_excel(writer, sheet_name=sheet_name, startrow=3, index=False)
    worksheet = writer.sheets[sheet_name]
    worksheet.write(0, 0, title, title_format)
    worksheet.write(1, 0, "Synthetic banking data generated for analytics reporting. Not real customer or financial data.", note_format)

    rows, columns = dataframe.shape
    if columns:
        worksheet.freeze_panes(4, 0)
        worksheet.autofilter(3, 0, max(3, rows + 3), columns - 1)
        for col_num, column_name in enumerate(dataframe.columns):
            worksheet.write(3, col_num, column_name, header_format)
            sample_values = dataframe[column_name].astype(str).head(100).tolist()
            width = min(max([len(str(column_name)), *[len(value) for value in sample_values]]) + 2, 35)
            worksheet.set_column(col_num, col_num, width)
            lowered = column_name.lower()
            if "amount" in lowered or "value" in lowered or "balance" in lowered or "flow" in lowered or "spend" in lowered:
                worksheet.set_column(col_num, col_num, max(width, 14), currency_format)
            elif "rate" in lowered or "percentage" in lowered or "share" in lowered or "growth" in lowered:
                worksheet.set_column(col_num, col_num, max(width, 12), percent_format)
            elif "count" in lowered or lowered.endswith("_key"):
                worksheet.set_column(col_num, col_num, max(width, 10), integer_format)
            elif "date" in lowered:
                worksheet.set_column(col_num, col_num, max(width, 12), date_format)
        if rows > 0 and columns > 0:
            worksheet.conditional_format(4, 0, rows + 3, columns - 1, {"type": "no_blanks", "format": workbook.add_format({"border": 1, "border_color": "#E6E6E6"})})


def _monthly_trends(model_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = model_tables["fact_transaction"]
    dim_date = model_tables["dim_date"]
    data = fact.merge(dim_date[["date_key", "month_start_date"]], on="date_key", how="left")
    return (
        data.groupby("month_start_date")
        .agg(
            transaction_count=("transaction_id", "count"),
            total_transaction_value=("transaction_amount", "sum"),
            approved_transaction_value=("approved_amount", "sum"),
            debit_transaction_value=("debit_amount", "sum"),
            credit_transaction_value=("credit_amount", "sum"),
            net_transaction_flow=("signed_transaction_amount", "sum"),
            average_transaction_amount=("transaction_amount", "mean"),
        )
        .reset_index()
    )


def _category_analysis(model_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = model_tables["fact_transaction"]
    category = model_tables["dim_transaction_category"]
    data = fact.merge(category[["transaction_category_key", "transaction_category"]], on="transaction_category_key", how="left")
    summary = (
        data.groupby("transaction_category")
        .agg(
            transaction_count=("transaction_id", "count"),
            total_transaction_value=("transaction_amount", "sum"),
            approved_transaction_value=("approved_amount", "sum"),
            average_transaction_amount=("transaction_amount", "mean"),
            declined_transaction_count=("is_declined", "sum"),
        )
        .reset_index()
    )
    summary["decline_rate"] = summary["declined_transaction_count"] / summary["transaction_count"]
    return summary.sort_values("total_transaction_value", ascending=False)


def _segment_analysis(model_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = model_tables["fact_transaction"]
    customer = model_tables["dim_customer"]
    data = fact.merge(customer[["customer_key", "customer_segment", "age_group"]], on="customer_key", how="left")
    summary = (
        data.groupby("customer_segment")
        .agg(
            active_customers=("customer_key", "nunique"),
            transaction_count=("transaction_id", "count"),
            total_transaction_value=("transaction_amount", "sum"),
            debit_transaction_value=("debit_amount", "sum"),
            credit_transaction_value=("credit_amount", "sum"),
            average_transaction_amount=("transaction_amount", "mean"),
        )
        .reset_index()
    )
    summary["transactions_per_customer"] = summary["transaction_count"] / summary["active_customers"]
    return summary.sort_values("total_transaction_value", ascending=False)


def _channel_analysis(model_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = model_tables["fact_transaction"]
    channel = model_tables["dim_channel"]
    data = fact.merge(channel[["channel_key", "transaction_channel"]], on="channel_key", how="left")
    summary = (
        data.groupby("transaction_channel")
        .agg(
            transaction_count=("transaction_id", "count"),
            total_transaction_value=("transaction_amount", "sum"),
            approved_count=("is_approved", "sum"),
            declined_count=("is_declined", "sum"),
        )
        .reset_index()
    )
    summary["approval_rate"] = summary["approved_count"] / summary["transaction_count"]
    summary["decline_rate"] = summary["declined_count"] / summary["transaction_count"]
    return summary.sort_values("transaction_count", ascending=False)


def _merchant_analysis(model_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = model_tables["fact_transaction"]
    merchant = model_tables["dim_merchant"]
    data = fact[["merchant_key", "transaction_id", "transaction_amount"]].merge(
        merchant[["merchant_key", "merchant_id", "merchant_name", "merchant_category"]],
        on="merchant_key",
        how="left",
    )
    return (
        data.groupby(["merchant_id", "merchant_name", "merchant_category"])
        .agg(
            transaction_count=("transaction_id", "count"),
            total_transaction_value=("transaction_amount", "sum"),
            average_transaction_amount=("transaction_amount", "mean"),
        )
        .reset_index()
        .sort_values("total_transaction_value", ascending=False)
        .head(100)
    )


def _status_analysis(model_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = model_tables["fact_transaction"]
    status = model_tables["dim_transaction_status"]
    data = fact.merge(status[["transaction_status_key", "transaction_status"]], on="transaction_status_key", how="left")
    summary = (
        data.groupby("transaction_status")
        .agg(transaction_count=("transaction_id", "count"), total_transaction_value=("transaction_amount", "sum"))
        .reset_index()
    )
    summary["transaction_share"] = summary["transaction_count"] / summary["transaction_count"].sum()
    return summary.sort_values("transaction_count", ascending=False)


def _quality_summary(model_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    issues = model_tables["fact_data_quality_issue"]
    if issues.empty:
        return pd.DataFrame(columns=["source_file", "rule_name", "severity", "issue_count"])
    return (
        issues.groupby(["source_file", "rule_name", "severity"])
        .size()
        .reset_index(name="issue_count")
        .sort_values("issue_count", ascending=False)
    )


def _add_charts(writer: pd.ExcelWriter) -> None:
    workbook = writer.book

    monthly = writer.sheets["Monthly Trends"]
    chart = workbook.add_chart({"type": "line"})
    chart.add_series({"name": "Transaction Count", "categories": "='Monthly Trends'!$A$5:$A$28", "values": "='Monthly Trends'!$B$5:$B$28"})
    chart.set_title({"name": "Monthly Transaction Count"})
    chart.set_legend({"position": "bottom"})
    monthly.insert_chart("I4", chart, {"x_scale": 1.3, "y_scale": 1.15})

    category = writer.sheets["Category Analysis"]
    bar_chart = workbook.add_chart({"type": "bar"})
    bar_chart.add_series({"name": "Total Value", "categories": "='Category Analysis'!$A$5:$A$18", "values": "='Category Analysis'!$C$5:$C$18"})
    bar_chart.set_title({"name": "Transaction Value by Category"})
    bar_chart.set_legend({"none": True})
    category.insert_chart("H4", bar_chart, {"x_scale": 1.25, "y_scale": 1.2})

    channel = writer.sheets["Channel Analysis"]
    column_chart = workbook.add_chart({"type": "column"})
    column_chart.add_series({"name": "Transaction Count", "categories": "='Channel Analysis'!$A$5:$A$10", "values": "='Channel Analysis'!$B$5:$B$10"})
    column_chart.set_title({"name": "Volume by Channel"})
    column_chart.set_legend({"none": True})
    channel.insert_chart("H4", column_chart, {"x_scale": 1.25, "y_scale": 1.15})


def generate_excel_report(
    model_tables: dict[str, pd.DataFrame],
    anomaly_flags: pd.DataFrame,
    reconciliation_report: pd.DataFrame,
    kpi_summary: pd.DataFrame,
    config: dict,
) -> str:
    logging.info("Starting Excel report generation")
    output_path = project_path(config["paths"]["excel_output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    workbook_tables = {
        "Executive Summary": kpi_summary,
        "Monthly Trends": _monthly_trends(model_tables),
        "Category Analysis": _category_analysis(model_tables),
        "Customer Segments": _segment_analysis(model_tables),
        "Channel Analysis": _channel_analysis(model_tables),
        "Merchant Analysis": _merchant_analysis(model_tables),
        "Transaction Status": _status_analysis(model_tables),
        "Anomaly Review": anomaly_flags.sort_values("anomaly_score", ascending=False).head(1000),
        "Data Quality": _quality_summary(model_tables),
        "Reconciliation": reconciliation_report,
    }

    with pd.ExcelWriter(output_path, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
        for sheet_name, dataframe in workbook_tables.items():
            _write_table(writer, sheet_name, dataframe, sheet_name)
        _add_charts(writer)

    logging.info("Excel report created at %s", output_path)
    return str(output_path)
