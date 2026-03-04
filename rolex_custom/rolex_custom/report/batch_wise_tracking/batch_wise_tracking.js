// Copyright (c) 2026, q and contributors
// For license information, please see license.txt

frappe.query_reports["Batch Wise Tracking"] = {
	"filters": [

        {
            "fieldname": "company",
            "label": "Company",
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
        },

        {
            "fieldname": "item_code",
            "label": "Item",
            "fieldtype": "Link",
            "options": "Item"
        },

        {
            "fieldname": "batch_no",
            "label": "Batch No",
            "fieldtype": "Link",
            "options": "Batch",
            "reqd": 1,
            "get_query": function() {
                let item = frappe.query_report.get_filter_value("item_code");

                if (item) {
                    return {
                        filters: {
                            item: item
                        }
                    };
                }
            }
        }

    ]
};
