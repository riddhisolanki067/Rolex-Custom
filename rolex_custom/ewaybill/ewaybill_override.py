import frappe
from frappe.utils import flt
from india_compliance.gst_india.utils.e_waybill import EWaybillData

def boot_session(bootinfo):
    apply_ewaybill_patch()

def apply_ewaybill_patch():
    import india_compliance.gst_india.utils.e_waybill as ewaybill_module

    if getattr(ewaybill_module, "_custom_stock_entry_patch_applied", False):
        return

    class CustomStockEntryEWaybillData(EWaybillData):
        def set_transaction_details(self):
            super().set_transaction_details()

            if self.doc.doctype != "Stock Entry":
                return

            self.transaction_details.total = flt(self.doc.custom_taxable_value)
            self.transaction_details.total_taxable_value = flt(self.doc.custom_taxable_value)
            self.transaction_details.total_non_taxable_value = 0

            self.transaction_details.total_cgst_amount = flt(self.doc.custom_cgst_amount)
            self.transaction_details.total_sgst_amount = flt(self.doc.custom_sgst_amount)
            self.transaction_details.total_igst_amount = flt(self.doc.custom_igst_amount)
            self.transaction_details.total_cess_amount = flt(
                self.doc.get("custom_cess_amount") or 0
            )

            self.transaction_details.grand_total = flt(self.doc.custom_total_value)

            current_total = (
                flt(self.transaction_details.total)
                + flt(self.transaction_details.total_cgst_amount)
                + flt(self.transaction_details.total_sgst_amount)
                + flt(self.transaction_details.total_igst_amount)
                + flt(self.transaction_details.total_cess_amount)
            )

            self.transaction_details.other_charges = flt(self.doc.custom_total_value) - current_total

            if abs(self.transaction_details.other_charges) < 0.01:
                self.transaction_details.other_charges = 0

            self.transaction_details.discount_amount = 0
            self.transaction_details.rounding_adjustment = 0

        def get_all_item_details(self):
            item_details_list = super().get_all_item_details()

            if self.doc.doctype != "Stock Entry":
                return item_details_list

            for row, item_details in zip(self.doc.items, item_details_list):
                if hasattr(row, "custom_taxable_value"):
                    item_details.taxable_value = abs(self.rounded(flt(row.custom_taxable_value)))

                if hasattr(row, "custom_cgst_amount"):
                    item_details.cgst_amount = abs(self.rounded(flt(row.custom_cgst_amount)))
                if hasattr(row, "custom_sgst_amount"):
                    item_details.sgst_amount = abs(self.rounded(flt(row.custom_sgst_amount)))
                if hasattr(row, "custom_igst_amount"):
                    item_details.igst_amount = abs(self.rounded(flt(row.custom_igst_amount)))

                item_details.total_value = abs(self.rounded(
                    flt(item_details.taxable_value)
                    + flt(item_details.get("cgst_amount", 0))
                    + flt(item_details.get("sgst_amount", 0))
                    + flt(item_details.get("igst_amount", 0))
                    + flt(item_details.get("cess_amount", 0))
                ))

            return item_details_list

    ewaybill_module.EWaybillData = CustomStockEntryEWaybillData
    ewaybill_module._custom_stock_entry_patch_applied = True