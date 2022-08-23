import frappe

def before_submit(self):
	frappe.errprint("before_submit")
	doc = frappe.get_doc("Employee", self.employee)
	doc.append("salary_structure_history", {
		"from_date": self.from_date,
		"salary_structure": self.salary_structure,
		"income_tax_slab": self.income_tax_slab
	})
	doc.save(ignore_permissions=True)

def on_cancel(self):
	frappe.errprint("cancel")
	doc = frappe.get_doc("Salary Structure History", {"salary_structure", self.salary_structure})
	doc.is_canceled = 1
	doc.save(ignore_permissions=True)
