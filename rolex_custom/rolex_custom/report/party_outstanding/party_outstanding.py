# Copyright (c) 2026, Rolex India

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	_validate_filters(filters)

	native_filters = frappe._dict(
		company=filters.company,
		report_date=getdate(filters.as_on_date),
		party_type=filters.party_type,
		party=[filters.party],
		# ERPNext v16's receivable/payable query expects this Link filter as a
		# scalar. Supplying a list generates invalid `account` SQL.
		party_account=filters.party_account,
		range="30, 60, 90, 120",
		ageing_based_on="Due Date",
		based_on_payment_terms=0,
		show_future_payments=0,
		show_remarks=0,
		in_party_currency=0,
	)

	if filters.party_type == "Customer":
		from erpnext.accounts.report.accounts_receivable.accounts_receivable import (
			execute as native_execute,
		)
	else:
		from erpnext.accounts.report.accounts_payable.accounts_payable import (
			execute as native_execute,
		)

	# Return ERPNext's native result intact, including its authoritative columns,
	# totals, ageing, chart and report summary where supplied.
	return native_execute(native_filters)


def _validate_filters(filters):
	required = {
		"company": _("Company"),
		"party_type": _("Party Type"),
		"party": _("Party"),
		"party_account": _("Party Account"),
		"as_on_date": _("As On Date"),
	}
	for fieldname, label in required.items():
		if not filters.get(fieldname):
			frappe.throw(_("{0} is required").format(label))

	if filters.party_type not in ("Customer", "Supplier"):
		frappe.throw(_("Party Type must be Customer or Supplier"))

	if not frappe.db.exists(filters.party_type, filters.party):
		frappe.throw(_("Invalid {0}: {1}").format(filters.party_type, filters.party))

	account = frappe.db.get_value(
		"Account",
		filters.party_account,
		["company", "account_type", "is_group"],
		as_dict=True,
	)
	if not account or account.company != filters.company or account.is_group:
		frappe.throw(_("Party Account must be a ledger account in the selected company"))

	expected_account_type = "Receivable" if filters.party_type == "Customer" else "Payable"
	if account.account_type != expected_account_type:
		frappe.throw(
			_("Party Account must be an {0} account for a {1}").format(
				expected_account_type, filters.party_type
			)
		)
