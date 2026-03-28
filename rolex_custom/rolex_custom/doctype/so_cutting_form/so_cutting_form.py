# Copyright (c) 2026, q and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SOCuttingForm(Document):
	pass
	def after_insert(doc):
		# Create new Sales Order Cutting document
		new_doc = frappe.new_doc("Sales Order Cutting")

		# Map parent fields
		new_doc.customer = doc.customer
		new_doc.transaction_date = doc.date
		new_doc.delivery_date = doc.delivery_date

		# Map child table (items)
		for item in doc.table_pxch:
			new_doc.append("items", {
				"item_code": item.item_code,
				"item_name": item.item_name,
				"qty": item.qty,
				"rate": item.rate,
				"amount": item.amount,
				"conversion_factor":1,
				"uom":item.uom,
		 		"custom_length":item.custom_length,
				"custom_no_of_pieces":item.custom_no_of_pieces,
				"custom_weight":item.custom_weight,
				"custom_per_mm_weight":item.custom_per_mm_weight,

	}) 

		# Save as Draft
		new_doc.insert(ignore_permissions=True)
		new_doc.submit()

	