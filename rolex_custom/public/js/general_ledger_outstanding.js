// Copyright (c) 2026, Rolex India
// Adds a party-specific outstanding action to the standard General Ledger
// without changing ERPNext core files.

(() => {
	const REPORT_NAME = "General Ledger";
	const BUTTON_LABEL = __("View Outstanding");
	const ALLOWED_PARTY_TYPES = new Set(["Customer", "Supplier"]);
	let retry_timer;

	function as_list(value) {
		if (!value) return [];
		if (Array.isArray(value)) return value.filter(Boolean);

		if (typeof value === "string") {
			try {
				const parsed = JSON.parse(value);
				if (Array.isArray(parsed)) return parsed.filter(Boolean);
			} catch (error) {
				// A normal Link value is not JSON.
			}
			return value.trim() ? [value.trim()] : [];
		}

		return [value].filter(Boolean);
	}

	function get_context(report) {
		const filters = {
			company: report.get_filter_value("company"),
			party_type: report.get_filter_value("party_type"),
			party: report.get_filter_value("party"),
			account: report.get_filter_value("account"),
			to_date: report.get_filter_value("to_date"),
		};
		const accounts = as_list(filters.account);
		const parties = as_list(filters.party);

		return {
			company: filters.company,
			party_type: filters.party_type,
			party: parties.length === 1 ? parties[0] : null,
			party_account: accounts.length === 1 ? accounts[0] : null,
			as_on_date: filters.to_date,
		};
	}

	function is_eligible(context) {
		return Boolean(
			context.company &&
				ALLOWED_PARTY_TYPES.has(context.party_type) &&
				context.party &&
				context.party_account &&
				context.as_on_date
		);
	}

	function remove_button(report) {
		if (report?.page?.remove_inner_button) {
			report.page.remove_inner_button(BUTTON_LABEL);
		}
	}

	function sync_button(report = frappe.query_report) {
		if (!report?.page || frappe.get_route()?.[1] !== REPORT_NAME) return;

		remove_button(report);
		const context = get_context(report);
		if (!is_eligible(context)) return;

		report.page.add_inner_button(BUTTON_LABEL, () => {
			frappe.set_route("query-report", "Party Outstanding", context);
		});
	}

	function wrap_callback(settings, callback_name) {
		const original = settings[callback_name];
		settings[callback_name] = function (...args) {
			const result = original?.apply(this, args);
			sync_button(args[0] || frappe.query_report);
			return result;
		};
	}

	function install() {
		clearTimeout(retry_timer);
		if (frappe.get_route()?.[1] !== REPORT_NAME) return;

		const settings = frappe.query_reports?.[REPORT_NAME];
		if (!settings || !frappe.query_report) {
			retry_timer = setTimeout(install, 150);
			return;
		}

		if (!settings.__rolex_party_outstanding_installed) {
			wrap_callback(settings, "onload");
			wrap_callback(settings, "after_datatable_render");
			settings.__rolex_party_outstanding_installed = true;
		}

		sync_button(frappe.query_report);
	}

	frappe.router.on("change", () => setTimeout(install, 0));
	frappe.after_ajax(install);
})();
