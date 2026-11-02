from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from rolex_custom import migrate


class TestOutstandingReportRouteMigration(IntegrationTestCase):
	@patch("rolex_custom.migrate.frappe.db.set_value")
	@patch("rolex_custom.migrate.frappe.db.get_value")
	@patch("rolex_custom.migrate.frappe.db.exists", return_value=False)
	def test_missing_tally_ledger_is_a_noop(self, _exists, get_value, set_value):
		migrate.after_migrate()
		get_value.assert_not_called()
		set_value.assert_not_called()

	@patch("rolex_custom.migrate.frappe.logger")
	@patch("rolex_custom.migrate.frappe.db.set_value")
	@patch(
		"rolex_custom.migrate.frappe.db.get_value",
		return_value='frappe.set_route("query-report", "Party Outstanding")',
	)
	@patch("rolex_custom.migrate.frappe.db.exists", return_value=True)
	def test_old_route_is_replaced_once(self, _exists, _get_value, set_value, _logger):
		migrate.after_migrate()
		set_value.assert_called_once_with(
			"Report",
			migrate.TALLY_GENERAL_LEDGER,
			"javascript",
			'frappe.set_route("query-report", "Rolex Party Outstanding")',
			update_modified=False,
		)

	@patch("rolex_custom.migrate.frappe.db.set_value")
	@patch(
		"rolex_custom.migrate.frappe.db.get_value",
		return_value='frappe.set_route("query-report", "Rolex Party Outstanding")',
	)
	@patch("rolex_custom.migrate.frappe.db.exists", return_value=True)
	def test_repeated_run_is_an_idempotent_noop(self, _exists, _get_value, set_value):
		migrate.after_migrate()
		set_value.assert_not_called()
