frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		
			frm.add_custom_button(
				__("All Copies (1 PDF)"),
				() => {
					window.open(
						"/api/method/rolex_custom.api.combined_print.download_combined_pdf" +
							"?name=" +
							encodeURIComponent(frm.doc.name),
						"_blank"
					);
				},
				__("Print")
			);
		
	},
});
