import frappe 

def execute():
    # Check if the old custom field still exists
    if not frappe.db.has_column("User", "signature"):
        frappe.log_error("Column 'signature' not found in User table", "User Signature Migration")
        return

    users = frappe.get_all(
        "User",
        filters={"signature": ["is", "set"]},
        fields=["name", "full_name", "signature"],
    )

    for user in users:
        if not frappe.db.exists("User Signature", {"user": user.name}):
            doc = frappe.get_doc({
                "doctype": "User Signature",
                "user": user.name,
                "full_name": user.full_name,
                "signature": user.signature
            })
            doc.insert(ignore_permissions=True)

    frappe.db.commit()