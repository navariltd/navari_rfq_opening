// Copyright (c) 2025, Navari Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Committee Note", {
  note_type(frm) {
    frm.trigger("validateRFQ");
    frm.trigger("generateContent");
  },
  evaluation_committee(frm) {
    frm.trigger("generateContent");
  },
  quotation(frm) {
    if (!frm.doc.quotation) {
      frm.set_value("generated_content", null);
    }
    frm.trigger("generateContent");
  },

  generateContent(frm) {
    if (frm.doc.quotation && frm.doc.note_type) {
      let args = {
        quotation: frm.doc.quotation,
        committee: frm.doc.committee,
        note_type: frm.doc.note_type,
        date: frm.doc.posting_date,
        evaluation_committee: frm.doc.evaluation_committee,
      };

      frappe.call({
        method:
          "rfq_opening_process.controllers.generate_template.generate_template",
        args: args,
        callback: function (res) {
          if (res && res.message) {
            frm.set_value("generated_content", res.message);
          }
        },
      });
    }
  },

  validateRFQ(frm) {
    if (!frm.doc.quotation) {
      frappe.msgprint({
        title: __("Error"),
        indicator: "red",
        message: __("Please select a Request for Quotation (RFQ)"),
      });

      return;
    }
  },
});
