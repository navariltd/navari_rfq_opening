import json
import frappe
from frappe import _
from erpnext.buying.doctype.request_for_quotation import request_for_quotation
from frappe.utils import cint, get_datetime

from erpnext.accounts.party import get_party_account_currency

def get_committee_members(committee_rec,rfq_name):
	committeemembers = frappe.db.sql("""
	SELECT
		cm.user_id,cm.full_name,cm.parent
	FROM
		`tabCommittee Member` as cm
	WHERE NOT EXISTS
		(
		SELECT
			todo.owner,todo.reference_name
		FROM
			`tabToDo` as todo
		WHERE
			cm.user_id = todo.owner
			AND todo.status = "Open"
			AND todo.reference_name =  %(rfqname)s
		)
	AND
		cm.parent = %(cm)s;""", {"cm": committee_rec.committee_name, "rfqname": rfq_name}, as_dict=1)

	return committeemembers

def make_quote_or_bid_opening_todo(committee,committeemember,rfq):
    todo = frappe.new_doc("ToDo")
    todo.priority = "High"
    todo.color = "#4f8ea8"
    todo.date = rfq.closing_date
    todo.due_time = rfq.closing_time
    todo.owner = committeemember
    todo.description = "Request for Quotation No: {0} Opening for {1} on: {2} at: {3}".format(rfq.name, committeemember, rfq.closing_date, rfq.closing_time)
    todo.reference_type = "Request for Quotation"
    todo.reference_name = rfq.name
    todo.assigned_by = frappe.session.user
    todo.allocated_to = committeemember
    todo.insert()

def create_quote_or_bid_opening(rfq):
	if frappe.db.exists("Committee", rfq.committee):
		committee = frappe.get_doc("Committee", rfq.committee)
		committeemembers = get_committee_members(committee,rfq.name)
		for cm in committeemembers:
			make_quote_or_bid_opening_todo(committee,cm.user_id,rfq)
	else:
		return

#Navari-check whether to skip supplier quotations opening (rfq paramater in case, this is per rfq), for now it will be system wide
def skip_supplier_quotation_opening_by_committee(rfq_name):
	if cint(frappe.db.get_single_value("RFQ Opening Settings", "skip_supplier_quotation_opening_by_committee")):
		return True

#Navari-count of received supplier quotations for each supplier and rfq
def count_of_received_supplier_quotations_for_supplier(supplier,rfq_name):
	received_sqs_count = frappe.db.sql("""
		SELECT
			count(sq.name) as count_of_received_sqs
		FROM
			`tabSupplier Quotation` as sq
		WHERE
			sq.supplier = %(suppliername)s
		AND
			sq.name in (SELECT 
						DISTINCT sqi.parent
					FROM 
						`tabSupplier Quotation Item` as sqi
					WHERE
						sqi.request_for_quotation = %(rfqname)s)""",
						{"suppliername": supplier, "rfqname": rfq_name})[0][0]

	return (received_sqs_count)

#Navari-count of received supplier quotations for each supplier and rfq
def allow_multiple_supplier_quotations_from_portal(supplier,rfq_name):
	if cint(frappe.db.get_single_value("RFQ Opening Settings", "allow_multiple_supplier_quotations_from_portal")):
		return True
	elif count_of_received_supplier_quotations_for_supplier(supplier,rfq_name) > 0:
		return False
	else:
		return True

def count_of_received_supplier_quotations_for_rfq(rfq_name):
	received_sqs_count = frappe.db.sql("""
		SELECT
			count(sq.name) as count_of_received_sqs
		FROM
			`tabSupplier Quotation` as sq
		WHERE
			sq.name in (SELECT 
						DISTINCT sqi.parent
					FROM 
						`tabSupplier Quotation Item` as sqi
					WHERE
						sqi.request_for_quotation = %(rfqname)s)""",
						{"rfqname": rfq_name})[0][0]
						
	return (received_sqs_count)

def get_minimum_expected_quotes_for_rfq(rfq_name):
	#get minimum expected quotes for rfq
	minimum_expected_quotes_for_rfq = frappe.get_value("Request for Quotation", rfq_name, "minimum_expected_quotes")

	return minimum_expected_quotes_for_rfq

def count_of_opened_quote_or_bid_todos(rfq_name):
	count_of_opened_quote_or_bid_entries_for_rfq = frappe.db.sql("""
		select
			count(name)
		from
			`tabToDo`
		where
			reference_name =  %(rfqname)s
			and status = "Closed";""",
			{"rfqname": rfq_name})[0][0]

	return count_of_opened_quote_or_bid_entries_for_rfq

def get_minimum_no_of_members_needed_to_open_sqs(rfq_name):
	#get committee associated with rfq
	rfq_committee = frappe.get_value("Request for Quotation", rfq_name, "committee")
	#get minimum members to open rfq
	minimum_no_of_members_needed_to_open_sqs = frappe.get_value("Committee", rfq_committee, "minimum_no_of_members_needed_to_open")

	return minimum_no_of_members_needed_to_open_sqs

def check_rfq_opening_date_and_time(rfq_name):
	#Get RFQ
	rfq = frappe.get_doc("Request for Quotation", rfq_name)
	#Date and Time Validations
	closing_datetime = "%s %s" % (rfq.closing_date,rfq.closing_time)
	if (get_datetime() < get_datetime(closing_datetime)):
		return False
	else:
		return True

def open_rfq_supplier_quotations(rfq_name):
		sqis = frappe.db.sql(""" 
			SELECT 
				distinct sqi.parent as sq
			FROM 
				`tabSupplier Quotation Item` as sqi
			WHERE
				sqi.request_for_quotation =  %(rfqname)s;""", {"rfqname": rfq_name}, as_dict=1)

		for sqi in sqis:
			supplierquotation = frappe.get_doc("Supplier Quotation", sqi.sq)
			if supplierquotation.submission_status == "Pending":
				supplierquotation.submission_status = "Open"
				supplierquotation.save(ignore_permissions=True)

@frappe.whitelist()
def send_supplier_emails_override(rfq_name):
    request_for_quotation.check_portal_enabled('Request for Quotation')
    rfq = frappe.get_doc("Request for Quotation", rfq_name)
    if rfq.docstatus==1:
        rfq.send_to_supplier()
        # Navari-Create Committee Member Opening Entries
        if not skip_supplier_quotation_opening_by_committee(rfq):
            create_quote_or_bid_opening(rfq)
		#End Navari

@frappe.whitelist()
def create_supplier_quotation_override(doc):
    if isinstance(doc, str):
        doc = json.loads(doc)
        
    try:
        #Navari (check for multiple sqs && closing date and time)
        if not allow_multiple_supplier_quotations_from_portal(doc.get('supplier'),doc.get('name')):
            frappe.throw(_("Supplier Quotation for Request for Quotation {0} already submitted".format(doc.get('name'))))
        closing_datetime = "%s %s" % (doc.get('closing_date'),doc.get('closing_time'))
        if (get_datetime() > get_datetime(closing_datetime)):
            frappe.throw(_("Submission Closing Date and Time {0} has already passed".format(closing_datetime)))
            #End Navari
            
        sq_doc = frappe.get_doc({
			"doctype": "Supplier Quotation",
			"supplier": doc.get('supplier'),
			"terms": doc.get("terms"),
			"company": doc.get("company"),
			"currency": doc.get('currency') or get_party_account_currency('Supplier', doc.get('supplier'), doc.get('company')),
			"buying_price_list": doc.get('buying_price_list') or frappe.db.get_value('Buying Settings', None, 'buying_price_list')
		})
        request_for_quotation.add_items(sq_doc, doc.get('supplier'), doc.get('items'))
        sq_doc.flags.ignore_permissions = True
        sq_doc.run_method("set_missing_values")
        #Navari set submission status to pending
        if not skip_supplier_quotation_opening_by_committee(doc.get('name')):
            sq_doc.submission_status = "Pending"
            #End Navari
        sq_doc.save()
        frappe.msgprint(_("Supplier Quotation {0} created").format(sq_doc.name))
        return sq_doc.name
    except Exception:
        return None

@frappe.whitelist()
def open_supplier_quotations(rfq_name):
	#TODO Validate date and time, move to client side
	if not check_rfq_opening_date_and_time:
		frappe.throw(_("Due Date and Time {0} is not yet"))
	received_sqs_for_rfq = count_of_received_supplier_quotations_for_rfq(rfq_name)
	minimum_expected_quotes_for_rfq = get_minimum_expected_quotes_for_rfq(rfq_name)
	opened_quote_or_bid_todos = count_of_opened_quote_or_bid_todos(rfq_name)
	minimum_no_of_members_needed_to_open_sqs = get_minimum_no_of_members_needed_to_open_sqs(rfq_name)

	if received_sqs_for_rfq >= minimum_expected_quotes_for_rfq:
		#Plus one for the incoming one
		if (opened_quote_or_bid_todos + 1) >= minimum_no_of_members_needed_to_open_sqs:
			#Open received quotations
			open_rfq_supplier_quotations(rfq_name)
			frappe.msgprint(_("{0} Supplier Quotations opened").format(received_sqs_for_rfq))		
	else:
		frappe.throw(_("The received supplier quote(s) for {0} is {1}, which is less than the expected number of {2} quotes".format(rfq_name, received_sqs_for_rfq, minimum_expected_quotes_for_rfq)))
		#TODO send mail to owner, and move above to client