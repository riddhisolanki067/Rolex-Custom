import frappe
from io import BytesIO
from pypdf import PdfWriter

# The print formats to combine, in the order they should appear in the PDF.
# Each format renders on its own page(s).
COMBINED_FORMATS = [
	"TAX INVOICE Print Format",
	"Tax Invoice 2nd copy",
	"Tax Invoice 3rd copy",
	"Tax Invoice 4th copy",
	"Job Invoice",
]


@frappe.whitelist()
def download_combined_pdf(name, doctype="Sales Invoice", formats=None):
	"""Return a single PDF containing several print formats of one document,
	each format starting on a new page.

	Each format is rendered to its own PDF via the normal print pipeline
	(letterheads/headers/footers intact) and the finished PDFs are merged at
	the file level, so page breaks between formats are automatic.
	"""
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("print")

	format_list = frappe.parse_json(formats) if formats else COMBINED_FORMATS

	writer = PdfWriter()
	for print_format in format_list:
		pdf_bytes = frappe.get_print(
			doctype,
			name,
			print_format=print_format,
			as_pdf=True,
		)
		writer.append(BytesIO(pdf_bytes))

	output = BytesIO()
	writer.write(output)
	writer.close()

	frappe.local.response.filename = f"{name}.pdf"
	frappe.local.response.filecontent = output.getvalue()
	frappe.local.response.type = "pdf"
