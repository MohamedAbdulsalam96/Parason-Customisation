# Copyright (c) 2022, Aerele Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from parason_customization.custom_py.attendance import add_attendance

class SyncAttendance(Document):
	@frappe.whitelist()
	def add_attendance(self):
		date = datetime.strptime(str(self.date), "%Y-%m-%d")
		if not (self.shift and self.date):
			frappe.throw("Shift and Date are mandatory")
		add_attendance([frappe._dict({"name":self.shift})], date)
