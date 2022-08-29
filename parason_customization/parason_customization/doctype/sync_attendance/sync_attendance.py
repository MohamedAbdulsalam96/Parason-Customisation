# Copyright (c) 2022, Aerele Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from parason_customization.custom_py.attendance import add_attendance, create_attendance

class SyncAttendance(Document):
	@frappe.whitelist()
	def add_attendance(self):
		if not (self.shift or self.employee):
			frappe.throw("Shift or Employee is mandatory")
		if not self.from_date:
			frappe.throw("From Date is mandatory")
		if not self.to_date:
			frappe.throw("To Date is mandatory")
		start = datetime.strptime(self.from_date, "%Y-%m-%d")
		end = datetime.strptime(self.to_date, "%Y-%m-%d")
		date_range = (end - start).days + 1
		for i in range(date_range):
			date = start + timedelta(days=i)
			if self.shift:
				add_attendance([frappe._dict({"name":self.shift})], date.date())
			elif self.employee:
				create_attendance(self.employee, date.date())
		frappe.msgprint("Attendance Created")
