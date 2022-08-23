from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
import frappe


class CustomSalarySlip(SalarySlip):
	def calculate_net_pay(self):
		super().calculate_net_pay()
		ot = frappe.db.get_value("")
