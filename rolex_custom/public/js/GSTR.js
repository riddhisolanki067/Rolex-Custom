frappe.ui.form.on("GSTR-1", {
    load_gstr1_data(frm) {
        // Runs every time data refreshes — inject our button into the filed tab
        requestAnimationFrame(() => inject_filtered_download_button(frm));
    },
});

function inject_filtered_download_button(frm) {
    const filed_tab = frm.gstr1?.tabs?.filed_tab;
    if (!filed_tab) return;

    const $btn_group = filed_tab.tabmanager?.wrapper?.find(".custom-button-group");
    if (!$btn_group?.length) return;

    // Avoid duplicate buttons on re-renders
    if ($btn_group.find('[data-label="download-b2c-hsn"]').length) return;

    // Only show when not yet filed (same condition as core "Download JSON")
    if (frm.gstr1?.status === "Filed") return;

    $(`<button class="btn btn-default ellipsis" data-label="download-b2c-hsn">
        Download B2C + HSN JSON
    </button>`)
        .appendTo($btn_group)
        .on("click", () => download_filtered_json(frm));
}

async function download_filtered_json(frm) {
    const { company_gstin, year, month_or_quarter } = frm.doc;

    frappe.show_progress(__("Preparing"), 40, 100, __("Filtering categories..."));

    try {
        const r = await frappe.call({
            method: "rolex_custom.api.gstr1_filtered.get_filtered_gstr1_json",
            args: { company_gstin, year, month_or_quarter },
        });

        frappe.hide_progress();

        if (!r.message?.data) {
            frappe.msgprint(__("No data found for B2C, HSN, and Document Issued categories."));
            return;
        }

        // Reuse India Compliance's own download helper
        india_compliance.trigger_file_download(
            JSON.stringify(r.message.data),
            r.message.filename,
        );

        frappe.show_alert({ message: __("Filtered JSON downloaded"), indicator: "green" });

    } catch (e) {
        frappe.hide_progress();
        frappe.msgprint(__("Download failed: ") + (e.message || "Unknown error"));
    }
}