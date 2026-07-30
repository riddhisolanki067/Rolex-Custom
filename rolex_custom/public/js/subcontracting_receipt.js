// Subcontracting Receipt — Job-DC references (tasks 1-3)
//  * "Fetch Job DCs" button fills the Job DC References table with the OPEN
//    Send-to-Subcontractor DCs of this receipt's Subcontracting Order(s)
//    (closed DCs are excluded server-side).            [task 1]
//  * Per-row "DC Closed" check stamps a date; the source Stock Entry is stamped
//    on submit (server-side on_submit).                [task 2]
//  * Per-row "Pull Batches -> RM" pushes that DC's batches into the supplied
//    (RM consumption) table.                           [task 3]

frappe.ui.form.on("Subcontracting Receipt", {
	fetch_original_doc_ref(frm) {
		fetch_job_dcs(frm);
	},
});

function scos_on_receipt(frm) {
	const from_rows = (rows) =>
		(rows || []).map((r) => r.subcontracting_order).filter(Boolean);
	return [
		...new Set([
			...from_rows(frm.doc.supplied_items),
			...from_rows(frm.doc.items),
		]),
	];
}

function fetch_job_dcs(frm) {
	const scos = scos_on_receipt(frm);
	if (!scos.length) {
		frappe.msgprint({
			title: __("No Subcontracting Order"),
			message: __(
				"This receipt has no Subcontracting Order to trace Job DCs from. Add items first."
			),
			indicator: "orange",
		});
		return;
	}
	frappe.call({
		method: "rolex_custom.api.subcontracting.get_job_dcs",
		args: { subcontracting_orders: JSON.stringify(scos) },
		freeze: true,
		freeze_message: __("Fetching open Job DCs..."),
		callback(r) {
			const dcs = r.message || [];
			frm.clear_table("doc_references");
			dcs.forEach((d) => {
				const row = frm.add_child("doc_references");
				Object.assign(row, d);
			});
			frm.refresh_field("doc_references");
			if (dcs.length) frm.dirty();
			frappe.show_alert({
				message: __("Fetched {0} open Job DC(s).", [dcs.length]),
				indicator: dcs.length ? "green" : "orange",
			});
		},
	});
}

frappe.ui.form.on("Subcontracting Job DC", {
	dc_closed(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.dc_closed) {
			if (!row.dc_closed_on)
				frappe.model.set_value(
					cdt,
					cdn,
					"dc_closed_on",
					frappe.datetime.now_date()
				);
		} else {
			frappe.model.set_value(cdt, cdn, "dc_closed_on", null);
		}
	},
	pull_batches(frm, cdt, cdn) {
		pull_dc_batches(frm, locals[cdt][cdn]);
	},
});

function pull_dc_batches(frm, row) {
	if (!row.job_dc) {
		frappe.show_alert({ message: __("No Job DC on this row."), indicator: "orange" });
		return;
	}
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
		args: { job_dc: row.job_dc },
		freeze: true,
		freeze_message: __("Reading batches from {0}...", [row.job_dc]),
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
			let msg = __("Filled {0} batch(es) from {1}.", [filled, row.job_dc]);
			if (ambiguous)
				msg +=
					" " +
					__("{0} row(s) had multiple candidate batches — pick those manually.", [
						ambiguous,
					]);
			if (skipped)
				msg += " " + __("{0} row(s) already had a batch (left untouched).", [skipped]);
			frappe.msgprint({
				title: __("RM Batch Pull"),
				message: msg,
				indicator: filled ? "green" : "orange",
			});
		},
	});
}
