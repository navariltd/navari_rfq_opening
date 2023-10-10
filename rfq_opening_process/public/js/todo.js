frappe.ui.form.on("ToDo", {
  onload: function (frm) {
    frm.set_query("reference_type", function (txt) {
      return {
        filters: {
          issingle: 0,
        },
      };
    });
  },
  refresh: function (frm) {
    if (frm.doc.reference_type && frm.doc.reference_name) {
      frm.add_custom_button(__(frm.doc.reference_name), function () {
        frappe.set_route(
          "Form",
          frm.doc.reference_type,
          frm.doc.reference_name
        );
      });
    }

    if (!frm.doc.__islocal) {
      //Navari for Usual ToDos
      if (frm.doc.reference_type !== "Request for Quotation") {
        if (frm.doc.status !== "Closed") {
          frm.add_custom_button(
            __("Close"),
            function () {
              frm.set_value("status", "Closed");
              frm.save(null, function () {
                // back to list
                frappe.set_route("List", "ToDo");
              });
            },
            "fa fa-check",
            "btn-success"
          );
        } else {
          frm.add_custom_button(
            __("Reopen"),
            function () {
              frm.set_value("status", "Open");
              frm.save();
            },
            null,
            "btn-default"
          );
        }
        frm.add_custom_button(
          __("New"),
          function () {
            frappe.new_doc("ToDo");
          },
          null,
          "btn-default"
        );
        //Navari for RFQs
      } else {
        if (frm.doc.status !== "Closed") {
          frm.add_custom_button(
            __("Open Quotes"),
            function () {
              let currentDateTime = new Date();
              let rfqOpeningDateTime = new parseDateTime(
                frm.doc.date,
                frm.doc.due_time
              );
              if (rfqOpeningDateTime <= currentDateTime) {
                //Call Open Quotes
                frappe.call({
                  method:
                    "rfq_opening_process.rfq_opening_process.doctype.request_for_quotation.request_for_quotation.open_supplier_quotations",
                  freeze: true,
                  args: {
                    rfq_name: frm.doc.reference_name,
                  },
                });
                frm.set_value("status", "Closed");
                frm.save(null, function () {
                  // back to list
                  frappe.set_route("List", "ToDo");
                });
              } else {
                msgprint(
                  __(
                    `Quote or Bid opening is only allowed on or after the Due Date and Time`
                  )
                );
              }
            },
            "fa fa-check",
            "btn-success"
          );
        }
      }
    }
  },
});

function parseDateTime(dateString, timeString) {
  const dateParts = dateString.split("-");
  const timeParts = timeString.split(":");

  // Extract year, month, day
  const year = parseInt(dateParts[0]);
  const month = parseInt(dateParts[1]) - 1; // Months are 0-indexed
  const day = parseInt(dateParts[2]);

  // Extract hours, minutes, and seconds
  const hours = parseInt(timeParts[0]);
  const minutes = parseInt(timeParts[1]);
  const seconds = parseInt(timeParts[2]);

  return new Date(year, month, day, hours, minutes, seconds);
}
