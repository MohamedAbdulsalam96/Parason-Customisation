import frappe
from hr.doctype.leave_control_panel.leave_control_panel import LeaveControlPanel

class CustomLeaveControlPanel(LeaveControlPanel):
	def get_employees(self):
		conditions, values = [], []
		for field in ["company", "employment_type", "employment_sub_type", "branch", "designation", "department"]:
			if self.get(field):
				conditions.append("{0}=%s".format(field))
				values.append(self.get(field))

		condition_str = " and " + " and ".join(conditions) if len(conditions) else ""

		e = frappe.db.sql(
			"select name from tabEmployee where status='Active' {condition}".format(
				condition=condition_str
			),
			tuple(values),
		)

		return e
