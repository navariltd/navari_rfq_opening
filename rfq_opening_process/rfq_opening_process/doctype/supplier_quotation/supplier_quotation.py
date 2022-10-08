import frappe

def get_permission_query_conditions(user):
	return """(`tabSupplier Quotation`.submission_status != 'Pending' and (`tabSupplier Quotation`.owner = '{user}' or `tabSupplier Quotation`.owner != '{user}'))"""\
		.format(user=frappe.session.user)