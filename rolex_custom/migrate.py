import frappe


TALLY_GENERAL_LEDGER = "Tally General Ledger"
OLD_REPORT = "Party Outstanding"
NEW_REPORT = "Rolex Party Outstanding"


def after_migrate():
	"""Point the database-defined Tally ledger at the app-owned Rolex report."""
	if not frappe.db.exists("Report", TALLY_GENERAL_LEDGER):
		return

	javascript = frappe.db.get_value("Report", TALLY_GENERAL_LEDGER, "javascript") or ""
	updated = javascript.replace(f'"{OLD_REPORT}"', f'"{NEW_REPORT}"')
	updated = updated.replace(f"'{OLD_REPORT}'", f"'{NEW_REPORT}'")

	if updated == javascript:
		return

	frappe.db.set_value(
		"Report",
		TALLY_GENERAL_LEDGER,
		"javascript",
		updated,
		update_modified=False,
	)
	frappe.logger("rolex_custom").info(
		"Updated %s routing from %s to %s",
		TALLY_GENERAL_LEDGER,
		OLD_REPORT,
		NEW_REPORT,
	)
