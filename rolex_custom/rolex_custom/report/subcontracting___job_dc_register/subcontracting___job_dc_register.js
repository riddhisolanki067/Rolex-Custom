// Copyright (c) 2026, q and contributors
frappe.query_reports["Subcontracting - Job DC Register"] = {
	filters: [
		{
			fieldname: "supplier",
			label: __("Subcontractor"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nPending\nClosed",
		},
	],
};
