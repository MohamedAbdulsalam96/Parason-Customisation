# Copyright (c) 2022, Aerele Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime

class OvertimeRequest(Document):
	def validate(self):
		if not frappe.db.get_value("Employee", self.employee, "allow_over_time"):
			frappe.throw("Employee: {0} doesn't allow for Over Time".format(self.employee))

	def before_save(self):
		if self.to_time < self.from_time:
			frappe.throw("To Date cannot be less than From Date")
		if self.to_time == self.from_time:
			frappe.throw("From and To time cannot be same")
		to_time = datetime.strptime(self.to_time.split('.')[0], "%H:%M:%S")
		from_time = datetime.strptime(self.from_time.split('.')[0], "%H:%M:%S")
		self.duration = (to_time - from_time).seconds

