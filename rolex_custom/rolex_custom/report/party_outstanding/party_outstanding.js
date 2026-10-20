// Copyright (c) 2026, Rolex India

frappe.query_reports["Party Outstanding"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "party_type",
			label: __("Party Type"),
			fieldtype: "Select",
			options: ["Customer", "Supplier"],
			reqd: 1,
		},
		{
			fieldname: "party",
			label: __("Party"),
			fieldtype: "Dynamic Link",
			options: "party_type",
			reqd: 1,
		},
		{
			fieldname: "party_account",
			label: __("Party Account"),
			fieldtype: "Link",
			options: "Account",
			reqd: 1,
			get_query() {
				const party_type = frappe.query_report.get_filter_value("party_type");
				return {
					filters: {
						company: frappe.query_report.get_filter_value("company"),
						account_type: party_type === "Customer" ? "Receivable" : "Payable",
						is_group: 0,
					},
				};
			},
		},
		{
			fieldname: "as_on_date",
			label: __("As On Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
	],
};
