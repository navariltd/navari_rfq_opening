import frappe


def execute():
	users = frappe.db.get_all("User", filters={"signature": ["is", "set"]}, fields=["name", "signature"])

	for user in users:
		frappe.get_doc({"doctype": "User Signature", "user": user.name, "signature": user.signature}).insert(
			ignore_permissions=True
		)

		frappe.db.set_value("User", user.name, "signature", None, update_modified=False)

	frappe.db.commit()
