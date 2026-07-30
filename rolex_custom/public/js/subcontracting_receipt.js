// Subcontracting Receipt — per-row controls on IC's "Original Document References"
// (doc_references / Dynamic Link) table. Bound to the Dynamic Link child but scoped
// to the doc_references field and to Stock Entry (Job DC) rows only.
//  * DC Closed check → source Stock Entry stamped on receipt submit (server on_submit). [task 2]
//  * Pull Batches → RM button → carries that DC's batches into supplied_items.          [task 3]

frappe.ui.form.on("Dynamic Link", {
	custom_dc_closed(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.parentfield !== "doc_references") return;
		if (row.custom_dc_closed && row.link_doctype !== "Stock Entry") {
			frappe.model.set_value(cdt, cdn, "custom_dc_closed", 0);
			frappe.show_alert({
				message: __("DC Closed applies only to Job DC (Stock Entry) rows."),
				indicator: "orange",
			});
		}
	},

	custom_pull_batches(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.parentfield !== "doc_references") return;
		if (row.link_doctype !== "Stock Entry") {
			frappe.show_alert({
				message: __("Batch pull applies only to Job DC (Stock Entry) rows."),
				indicator: "orange",
			});
			return;
		}
		if (!row.link_name) return;
		pull_dc_batches(frm, row.link_name);
	},
});

function pull_dc_batches(frm, job_dc) {
	const supplied = frm.doc.supplied_items || [];
	if (!supplied.length) {
		frappe.msgprint({
			title: __("No RM rows"),
			message: __("There are no supplied (raw material) rows to fill yet."),
			indicator: "orange",
		});
		return;
	}
	frappe.call({
		method: "rolex_custom.api.subcontracting.get_dc_rm_batches",
		args: { job_dc },
		freeze: true,
		freeze_message: __("Reading batches from {0}...", [job_dc]),
		callback(r) {
			const by_item = {};
			(r.message || []).forEach((l) => {
				(by_item[l.item_code] = by_item[l.item_code] || new Set()).add(l.batch_no);
			});
			let filled = 0,
				ambiguous = 0,
				skipped = 0;
			supplied.forEach((s) => {
				if (s.batch_no) {
					skipped++;
					return; // never clobber an existing allocation
				}
				const batches = [...(by_item[s.rm_item_code] || [])];
				if (batches.length === 1) {
					s.use_serial_batch_fields = 1;
					s.batch_no = batches[0];
					filled++;
				} else if (batches.length > 1) {
					ambiguous++;
				}
			});
			frm.refresh_field("supplied_items");
			if (filled) frm.dirty();
			let msg = __("Filled {0} batch(es) from {1}.", [filled, job_dc]);
			if (ambiguous)
				msg += " " + __("{0} row(s) had multiple candidate batches — pick those manually.", [ambiguous]);
			if (skipped) msg += " " + __("{0} row(s) already had a batch (left untouched).", [skipped]);
			frappe.msgprint({ title: __("RM Batch Pull"), message: msg, indicator: filled ? "green" : "orange" });
		},
	});
}
