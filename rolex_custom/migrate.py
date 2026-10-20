import frappe


LEGACY_REPORT = "Party Outstanding"
LEGACY_BACKUP = "Party Outstanding Legacy Backup"


def before_migrate():
	"""Preserve the old custom report so the app-owned report can be synced."""
	if not frappe.db.exists("Report", LEGACY_REPORT):
		return

	is_standard = frappe.db.get_value("Report", LEGACY_REPORT, "is_standard")
	if is_standard != "No":
		return

	if frappe.db.exists("Report", LEGACY_BACKUP):
		frappe.throw(
			"Cannot install the standard Party Outstanding report because "
			f"{LEGACY_BACKUP} already exists."
		)

	frappe.rename_doc(
		"Report",
		LEGACY_REPORT,
		LEGACY_BACKUP,
		force=True,
		ignore_permissions=True,
		show_alert=False,
	)
