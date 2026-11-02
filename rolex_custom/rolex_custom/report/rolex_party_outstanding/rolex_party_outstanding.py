# Copyright (c) 2026, Rolex India

import frappe
from frappe import _


# ERPNext / Frappe v16 Script Report
# Report Name: Rolex Party Outstanding
# VERSION: 11-supplier-net-before-tds
def execute(filters=None):
	return _run(frappe._dict(filters or {}))


def _run(filters):
	filters = filters or {}
	if not filters.get("company"):
		filters["company"] = frappe.db.get_default("company") or "Rolex India"
	if not filters.get("report_date"):
		filters["report_date"] = frappe.utils.nowdate()
	if not filters.get("party_type"):
		filters["party_type"] = "Customer"
	party_type = filters.get("party_type")
	# Single Party link + legacy customer/supplier filters
	selected_party = filters.get("party")
	if not selected_party:
		if party_type == "Supplier":
			selected_party = filters.get("supplier")
		else:
			selected_party = filters.get("customer")
	show_party_col = not selected_party
	invoice_no_label = _("Invoice / Payment No")
	if party_type == "Supplier":
		invoice_no_label = _("Bill / Payment No")
	# ---------------------------------------------------------
	# COLUMNS - Rolex presentation (exactly six visible columns)
	columns = [
		{"label": _("Date"), "fieldname": "invoice_date", "fieldtype": "Date", "width": 110},
		{"label": _("Voucher No."), "fieldname": "invoice_no", "fieldtype": "Data", "width": 160},
		{"label": _("Invoice Amount"), "fieldname": "invoice_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": _("Pending Amount"), "fieldname": "pending_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 110},
		{"label": _("Payment Tracking"), "fieldname": "payment_trace", "fieldtype": "Data", "width": 210},
	]
	if show_party_col:
		columns.insert(0, {
			"label": _("Party"),
			"fieldname": "party",
			"fieldtype": "Link",
			"options": party_type,
			"width": 220,
		})
	# PAYMENT LEDGER
	# ---------------------------------------------------------
	company = filters.get("company")
	report_date = filters.get("report_date")
	conditions = [
		"ple.company = %(company)s",
		"ple.party_type = %(party_type)s",
		"ple.delinked = 0",
		"ple.posting_date <= %(report_date)s",
	]
	values = {
		"company": company,
		"report_date": report_date,
		"party_type": party_type,
	}
	if party_type == "Supplier":
		conditions.append(
			"""
			ple.account IN (
				SELECT leaf.name
				FROM `tabAccount` leaf
				INNER JOIN `tabAccount` root
					ON root.name = 'Creditors - RI'
					AND root.company = %(company)s
				WHERE leaf.company = %(company)s
					AND leaf.is_group = 0
					AND leaf.lft >= root.lft
					AND leaf.rgt <= root.rgt
					AND leaf.name NOT LIKE '%%Payroll%%'
			)
			"""
		)
		default_voucher_type = "Purchase Invoice"
	else:
		conditions.append(
			"""
			ple.account IN (
				SELECT name
				FROM `tabAccount`
				WHERE parent_account = 'Debtors - RI'
					AND company = %(company)s
					AND is_group = 0
			)
			"""
		)
		default_voucher_type = "Sales Invoice"
	if selected_party:
		conditions.append("ple.party = %(party)s")
		values["party"] = selected_party
	if filters.get("cost_center"):
		conditions.append("ple.cost_center = %(cost_center)s")
		values["cost_center"] = filters.get("cost_center")
	where_sql = " AND ".join(conditions)
	query = (
		"SELECT ple.account, ple.party, ple.voucher_type, ple.voucher_no, "
		"ple.against_voucher_type, ple.against_voucher_no, ple.posting_date, "
		"ple.due_date, ple.amount, ple.account_currency "
		"FROM `tabPayment Ledger Entry` ple WHERE "
		+ where_sql
		+ " ORDER BY ple.posting_date, ple.party, ple.voucher_no"
	)
	ple_rows = frappe.db.sql(query, values, as_dict=1)
	# ---------------------------------------------------------
	# BUILD OUTSTANDING BALANCES
	# ---------------------------------------------------------
	balances = {}
	for ple in ple_rows:
		against_no = ple.get("against_voucher_no")
		against_type = ple.get("against_voucher_type") or default_voucher_type
		voucher_no = ple.get("voucher_no")
		voucher_type = ple.get("voucher_type")
		account = ple.get("account")
		party = ple.get("party")
		currency = ple.get("account_currency")
		amt = frappe.utils.flt(ple.get("amount"))
		if against_no and against_no != voucher_no:
			key = (
				account
				+ "||"
				+ party
				+ "||"
				+ against_type
				+ "||"
				+ against_no
			)
			row = balances.get(key)
			if not row:
				row = {
					"account": account,
					"party": party,
					"voucher_type": against_type,
					"our_voucher": against_no,
					"invoice_no": against_no,
					"invoice_date": None,
					"due_date": None,
					"invoice_amount": 0.0,
					"pending_amount": 0.0,
					"settlements": [],
					"currency": currency,
				}
				balances[key] = row
			row["pending_amount"] = (
				frappe.utils.flt(row.get("pending_amount")) + amt
			)
			row["settlements"].append({
				"posting_date": ple.get("posting_date"),
				"voucher_type": voucher_type,
				"voucher_no": voucher_no,
				"amount": amt,
			})
		else:
			key = (
				account
				+ "||"
				+ party
				+ "||"
				+ str(voucher_type)
				+ "||"
				+ str(voucher_no)
			)
			row = balances.get(key)
			if not row:
				row = {
					"account": account,
					"party": party,
					"voucher_type": voucher_type,
					"our_voucher": voucher_no,
					"invoice_no": voucher_no,
					"invoice_date": None,
					"due_date": None,
					"invoice_amount": 0.0,
					"pending_amount": 0.0,
					"settlements": [],
					"currency": currency,
				}
				balances[key] = row
			row["pending_amount"] = (
				frappe.utils.flt(row.get("pending_amount")) + amt
			)
			# This is mainly useful for advances/payment entries.
			# Actual supplier invoice value is replaced later from Purchase Invoice.
			if amt > 0:
				row["invoice_amount"] = (
					frappe.utils.flt(row.get("invoice_amount")) + amt
				)
			elif amt < 0:
				# Unallocated payment / advance
				row["invoice_amount"] = (
					frappe.utils.flt(row.get("invoice_amount")) + (-amt)
				)
			if ple.get("posting_date"):
				if (
					not row.get("invoice_date")
					or ple.get("posting_date") < row.get("invoice_date")
				):
					row["invoice_date"] = ple.get("posting_date")
			if ple.get("due_date"):
				row["due_date"] = ple.get("due_date")
	# ---------------------------------------------------------
	# LOAD SALES / PURCHASE INVOICE DETAILS
	# ---------------------------------------------------------
	doc_names = []
	for key in balances:
		row = balances[key]
		if row.get("voucher_type") == default_voucher_type:
			doc_names.append(row.get("our_voucher"))
	doc_map = {}
	if doc_names:
		chunk_size = 500
		i = 0
		while i < len(doc_names):
			end = i + chunk_size
			chunk = doc_names[i:end]
			if party_type == "Supplier":
				# Supplier Invoice Amount:
				# Rounded Total + TDS deducted
				doc_rows = frappe.db.sql(
					"""
					SELECT
						pi.name,
						pi.due_date,
						pi.posting_date,
						pi.rounded_total,
						pi.bill_no,
						COALESCE(
							(
								SELECT SUM(ABS(ptc.tax_amount))
								FROM `tabPurchase Taxes and Charges` ptc
								WHERE ptc.parent = pi.name
									AND ptc.parenttype = 'Purchase Invoice'
									AND ptc.add_deduct_tax = 'Deduct'
									AND (
										UPPER(COALESCE(ptc.account_head, '')) LIKE '%%TDS%%'
										OR UPPER(COALESCE(ptc.description, '')) LIKE '%%TDS%%'
									)
							),
							0
						) AS tds_amount
					FROM `tabPurchase Invoice` pi
					WHERE pi.name IN %(names)s
					""",
					{"names": chunk},
					as_dict=1,
				)
			else:
				doc_rows = frappe.db.sql(
					"""
					SELECT
						name,
						due_date,
						posting_date,
						rounded_total
					FROM `tabSales Invoice`
					WHERE name IN %(names)s
					""",
					{"names": chunk},
					as_dict=1,
				)
			for doc in doc_rows:
				doc_map[doc.get("name")] = doc
			i = end
	# ---------------------------------------------------------
	# PREPARE REPORT ROWS
	# ---------------------------------------------------------
	# Only explicit, submitted invoice-to-receipt links qualify for tracing.
	receipts_by_invoice = {}
	if party_type == "Supplier" and doc_names:
		for start in range(0, len(doc_names), 500):
			receipt_links = frappe.db.sql(
				"SELECT DISTINCT pii.parent AS invoice, pr.name AS receipt "
				"FROM `tabPurchase Invoice Item` pii "
				"INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent "
				"INNER JOIN `tabPurchase Receipt` pr ON pr.name = pii.purchase_receipt "
				"WHERE pii.parent IN %(names)s AND pi.docstatus = 1 AND pr.docstatus = 1 "
				"AND pi.company = %(company)s AND pr.company = %(company)s "
				"ORDER BY pii.parent, pr.name",
				{"names": doc_names[start:start + 500], "company": company}, as_dict=1,
			)
			for link in receipt_links:
				invoice = link.get("invoice")
				if invoice not in receipts_by_invoice:
					receipts_by_invoice[invoice] = []
				receipts_by_invoice[invoice].append(link.get("receipt"))

	company_currency = frappe.db.get_value(
		"Company",
		company,
		"default_currency",
	)
	report_dt = frappe.utils.getdate(report_date)
	overdue_only = filters.get("overdue_only")
	show_zero = filters.get("show_zero_outstanding")
	rows = []
	total_advances = 0.0
	for key in balances:
		row = balances[key]
		pending = frappe.utils.flt(
			row.get("pending_amount"),
			2,
		)
		if pending == 0 and not show_zero:
			continue
		# Negative pending = advance / credit
		is_advance = 0
		if pending < 0:
			is_advance = 1
		our_voucher = row.get("our_voucher")
		voucher_type = row.get("voucher_type") or default_voucher_type
		# This report presents outstanding invoices only, not unallocated advances.
		if voucher_type != default_voucher_type:
			continue
		display_no = our_voucher
		doc = doc_map.get(our_voucher)
		if doc and not is_advance:
			if not row.get("due_date"):
				row["due_date"] = doc.get("due_date")
			if not row.get("invoice_date"):
				row["invoice_date"] = doc.get("posting_date")
			# -------------------------------------------------
			# SUPPLIER INVOICE VALUE
			# -------------------------------------------------
			if party_type == "Supplier":
				rounded_total = frappe.utils.flt(doc.get("rounded_total"))
				tds_amount = frappe.utils.flt(doc.get("tds_amount"))
				row["invoice_amount"] = rounded_total + tds_amount
				if doc.get("bill_no"):
					display_no = doc.get("bill_no")
			else:
				# Customer logic stays unchanged
				if (
					not row.get("invoice_amount")
					and doc.get("rounded_total")
				):
					row["invoice_amount"] = frappe.utils.flt(
						doc.get("rounded_total")
					)
		elif doc and is_advance:
			if not row.get("invoice_date"):
				row["invoice_date"] = doc.get("posting_date")
		# ---------------------------------------------------------
		# OVERDUE FILTER
		# ---------------------------------------------------------
		due_date = row.get("due_date")
		if overdue_only:
			if is_advance:
				continue
			if not due_date:
				continue
			if frappe.utils.getdate(due_date) >= report_dt:
				continue
		# ---------------------------------------------------------
		# OVERDUE DAYS
		# ---------------------------------------------------------
		overdue_days = None
		if not is_advance:
			overdue_days = 0
			if due_date:
				diff = frappe.utils.date_diff(
					report_dt,
					frappe.utils.getdate(due_date),
				)
				if diff > 0:
					overdue_days = diff
		else:
			due_date = None
			total_advances = (
				total_advances + (-pending)
			)
		# ---------------------------------------------------------
		# INVOICE AMOUNT
		# ---------------------------------------------------------
		inv_amt = frappe.utils.flt(
			row.get("invoice_amount"),
			2,
		)
		if is_advance and inv_amt == 0:
			inv_amt = -pending
		settlement_entries = []
		if party_type == "Supplier" and doc and frappe.utils.flt(doc.get("tds_amount")):
			settlement_entries.append({
				"posting_date": doc.get("posting_date"),
				"label": "TDS / Withholding",
				"voucher_type": "Purchase Invoice",
				"voucher_no": our_voucher,
				"amount": -frappe.utils.flt(doc.get("tds_amount"), 2),
			})
		for settlement in row.get("settlements") or []:
			settlement_type = settlement.get("voucher_type") or ""
			settlement_label = settlement_type or "Other Allocation"
			if settlement_type == "Payment Entry": settlement_label = "Payment Entry"
			elif settlement_type == "Journal Entry": settlement_label = "Journal Entry"
			elif party_type == "Supplier" and settlement_type == "Purchase Invoice": settlement_label = "Debit Note"
			elif party_type == "Customer" and settlement_type == "Sales Invoice": settlement_label = "Credit Note"
			settlement_entries.append({
				"posting_date": settlement.get("posting_date"),
				"label": settlement_label,
				"voucher_type": settlement_type,
				"voucher_no": settlement.get("voucher_no"),
				"amount": frappe.utils.flt(settlement.get("amount"), 2),
			})
		settlement_total = 0.0
		for settlement in settlement_entries:
			settlement_total += frappe.utils.flt(settlement.get("amount"), 2)
		settlement_difference = frappe.utils.flt(pending - (inv_amt + settlement_total), 2)
		if abs(settlement_difference) > 0.005:
			settlement_entries.append({
				"posting_date": report_date,
				"label": "Other Adjustment (Payment Ledger reconciliation)",
				"voucher_type": "",
				"voucher_no": "",
				"amount": settlement_difference,
			})
			settlement_difference = 0.0
		sort_date = ""
		if row.get("invoice_date"):
			sort_date = str(row.get("invoice_date"))
		rows.append(
			{
				"party": row.get("party"),
				"invoice_date": row.get("invoice_date"),
				"invoice_no": display_no,
				"invoice_amount": inv_amt,
				"pending_amount": pending,
				"settlement_entries": settlement_entries,
				"settlement_difference": settlement_difference,
				"due_date": due_date,
				"overdue_days": overdue_days,
				"voucher_type": voucher_type,
				"our_voucher": our_voucher,
				"currency": row.get("currency") or company_currency,
				"sort_party": row.get("party") or "",
				"sort_date": sort_date,
				"is_advance": is_advance,
			}
		)
	# ---------------------------------------------------------
	# SORT
	# ---------------------------------------------------------
	def sort_key(r):
		return (
			(r.get("sort_party") or "")
			+ "||"
			+ (r.get("sort_date") or "")
			+ "||"
			+ (r.get("invoice_no") or "")
		)
	rows.sort(key=sort_key)
	# ---------------------------------------------------------
	# TOTALS
	# ---------------------------------------------------------
	total_invoice = 0.0
	total_pending = 0.0
	for r in rows:
		total_invoice = (
			total_invoice
			+ frappe.utils.flt(r.get("invoice_amount"))
		)
		total_pending = (
			total_pending
			+ frappe.utils.flt(r.get("pending_amount"))
		)
	out = []
	for r in rows:
		item = {
			"party": r.get("party"),
			"invoice_date": r.get("invoice_date"),
			"invoice_no": r.get("invoice_no"),
			"invoice_amount": r.get("invoice_amount"),
			"pending_amount": r.get("pending_amount"),
			"settlement_entries": r.get("settlement_entries") or [],
			"settlement_difference": r.get("settlement_difference") or 0.0,
			"due_date": r.get("due_date"),
			"overdue_days": r.get("overdue_days"),
			"voucher_type": r.get("voucher_type"),
			"our_voucher": r.get("our_voucher"),
			"currency": r.get("currency"),
			"is_advance": r.get("is_advance"),
		}
		if party_type == "Supplier" and r.get("voucher_type") == "Purchase Invoice":
			item["payment_trace"] = ", ".join(receipts_by_invoice.get(r.get("our_voucher")) or [])
		out.append(item)
	# ---------------------------------------------------------
	# TOTAL ROW
	# ---------------------------------------------------------
	# Frappe adds the total row; its table footer recalculates after inline filters.
	# ---------------------------------------------------------
	# SUMMARY
	# ---------------------------------------------------------
	advance_label = _("Customer Advances")
	if party_type == "Supplier":
		advance_label = _("Supplier Advances")
	summary = [
		{"value": total_invoice, "label": _("Total Invoice Amount"), "datatype": "Currency", "currency": company_currency},
		{
			"value": frappe.utils.flt(total_pending),
			"label": _("Total Pending"),
			"datatype": "Currency",
		},
		{
			"value": frappe.utils.flt(total_advances),
			"label": advance_label,
			"datatype": "Currency",
		},
	]
	return [
		columns,
		out,
		None,
		None,
		summary,
	]
