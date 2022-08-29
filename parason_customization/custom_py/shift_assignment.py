import frappe
from datetime import datetime, timedelta, date
from parason_customization.custom_py.attendance import create_attendance


def on_submit(self, method):
	start = datetime.strptime(self.start_date, "%Y-%m-%d")
	end = datetime.strptime(self.end_date, "%Y-%m-%d")
	date_range = (end - start).days + 1
	for i in range(date_range):
		cur_date = (start + timedelta(days=i)).date()
		if cur_date < date.today():
			create_attendance(self.employee, cur_date, self.shift_type)
