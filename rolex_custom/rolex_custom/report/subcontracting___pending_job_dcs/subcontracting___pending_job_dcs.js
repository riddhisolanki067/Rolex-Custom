// Copyright (c) 2026, q and contributors
frappe.query_reports["Subcontracting - Pending Job DCs"] = {
	filters: [
		{
			fieldname: "supplier",
			label: __("Subcontractor"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
	],
};
