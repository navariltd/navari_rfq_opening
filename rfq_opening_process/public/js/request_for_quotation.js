frappe.ui.form.on("Request for Quotation", {
    refresh: function(frm) {
        frappe.db.get_single_value("RFQ Opening Settings", "require_mandatory_on_rfq").then(value => {
            frm.set_df_property("minimum_expected_quotes", "reqd", value ? 1 : 0);
            frm.set_df_property("committee", "reqd", value ? 1 : 0);
            frm.set_df_property("closing_date", "reqd", value ? 1 : 0);
            frm.set_df_property("closing_time", "reqd", value ? 1 : 0);
        });
    }
});
