// Copyright (c) 2026, Rolex India and contributors

frappe.query_reports["Pending Sales Orders Size Wise"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "from_date",
			label: __("Order Date From"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("Delivery Date Up To"),
			fieldtype: "Date",
		},
		{
			fieldname: "overdue_only",
			label: __("Overdue Only"),
			fieldtype: "Check",
			default: 0,
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (column.fieldname === "pending_qty") {
			return `<strong style="color:var(--orange-600)">${value}</strong>`;
		}
		if (column.fieldname === "delivery_date" && data.is_overdue) {
			return `<span style="color:var(--red-600);font-weight:600">${value}</span>`;
		}
		if (column.fieldname === "delay_days" && data.is_overdue) {
			return `<span class="indicator-pill red">${value} ${__("days")}</span>`;
		}
		if (column.fieldname === "size_description") {
			return `<span title="${frappe.utils.escape_html(data.size_description || "")}">${value}</span>`;
		}
		return value;
	},
};
