from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
import frappe


class CustomSalarySlip(SalarySlip):
	def update_component_row(
		self,
		component_data,
		amount,
		component_type,
		additional_salary=None,
		is_recurring=0,
		data=None,
		default_amount=None,
	):
		ot_component = frappe.db.get_value("Company", self.company, "over_time_component")
		if component_data.salary_component == ot_component:
			ot = frappe.db.sql(""" select sum(duration) from `tabOvertime Request` where employee='{0}' and from_time>='{1}' and to_time<='{2}'
						""".format(self.employee, self.start_date, self.end_date))
			ot = ot[0][0] or 0 if ot else 0
			if ot:
				ot = ot / 60 // 30 / 2
			amount = amount * ot
		super().update_component_row(component_data, amount, component_type, additional_salary, is_recurring, data, default_amount)
