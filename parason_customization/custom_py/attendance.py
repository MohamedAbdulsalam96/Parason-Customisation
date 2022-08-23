import frappe
from datetime import datetime, timedelta, date




def add_attendance(shifts=None, sync_date= None):
	cur_time = datetime.now()
	cur_shift_time = (cur_time + timedelta(hours=1)).time()
	if not sync_date:
		sync_date = (cur_time - timedelta(days=1)).date()
	if not shifts:
		shifts = get_shifts(cur_time, cur_shift_time)
	margin_start_date = cur_time - timedelta(days=1)
	margin_end_date = cur_time
	for shift in shifts:
		shift = shift.name
		shift_start = frappe.db.get_value("Shift Type", shift, "start_time")
		shift_end = frappe.db.get_value("Shift Type", shift, "end_time")
		shift_start = datetime.strptime(str(sync_date.date())+" "+str(shift_start), "%Y-%m-%d %H:%M:%S")
		shift_end = datetime.strptime(str(sync_date.date())+" "+str(shift_end), "%Y-%m-%d %H:%M:%S")
		margin_start_date = shift_start - timedelta(hours=1)
		margin_end_date = shift_end + timedelta(hours=7)
		employees = get_employee(shift, sync_date)
		for employee in employees:
			employee = employee.employee
			#duplicate = check_duplication(str(sync_date‌), employee)
			duplicate = check_duplication(str(sync_date), employee)
			if duplicate:
				return
			company = frappe.db.get_value("Employee", employee, "company")
			holiday_list = get_holiday_list(employee, shift, company)
			checkin_details = get_checkin_details(employee, margin_start_date, margin_end_date)
			if len(checkin_details) in [0, 1]:
				leave = frappe.db.get_value("Leave Application", {"employee":employee, "from_date":[">=", str(sync_date)],
					"to_date":["<=", str(sync_date)], "docstatus": 1})
				frappe.errprint(holiday_list)
				is_holiday = frappe.get_value("Holiday", {"holiday_date": str(sync_date.date()), "parent":holiday_list})
				frappe.errprint(is_holiday)
				doc = frappe.new_doc("Attendance")
				doc.employee = employee
				doc.shift = shift
				doc.in_time = "00:00:00"
				doc.out_time = "00:00:00"
				doc.attendance_date = sync_date
				doc.status = "On Leave"
				if is_holiday:
					week_off = frappe.get_value("Holiday", is_holiday, "weekly_off")
					frappe.errprint(week_off)
					if week_off:
						doc.status = "On Leave" #"Week Off"
				elif leave:
					doc.status = "On Leave"
					doc.leave_application = leave
					doc.leave_type = frappe.db.get_value("Leave Application", leave, "leave_type")
					is_holiday = frappe.get_value("Holiday", {"holiday_date": str(sync_date), "parent":holiday_list})
					if is_holiday:
						doc.leave_application = ''
						doc.leave_type = ""
						week_off = frappe.get_value("Holiday", is_holiday, "weekly_off")
						if week_off:
							doc.status = "On Leave" #"Week Off"
				else:
					doc.status = "Absent"
				doc.save(ignore_permissions = True)
				doc.submit()
			else:
				checkin = checkin_details[0]
				checkout = checkin_details[-1]
				doc = frappe.new_doc("Attendance")
				doc.employee = employee
				doc.shift = shift
				doc.in_time = checkin
				doc.out_time = checkout
				doc.attendance_date = sync_date
				duration = checkout - checkin
				duration = duration.seconds / 60 / 60
				doc.status = "Present"
				is_half_day = False
				if duration < 8 and duration >= 4:
					is_half_day = True
				if duration < 4:
					doc.status = "Absent"
				if frappe.db.get_value("Employee", employee, "allow_over_time"):
					ot = checkout - shift_end
					if ot.seconds > 0 and ot.seconds / 60 > 30:
						ot_doc = frappe.new_doc("Overtime Request")
						ot_doc.employee = employee
						ot_doc.company = company
						ot_doc.posting_date = sync_date
						ot_doc.overtime_date = sync_date
						ot_doc.from_time = shift_end
						ot_doc.to_time = checkout
						ot_doc.save(ignore_permissions=True)
						ot_doc.submit()
				doc.save(ignore_permissions=True)
				doc.submit()
	frappe.msgprint("Attendace records are added")

def check_duplication(attendance_date, employee):
	return frappe.db.exists("Attendance", {'attendance_date':attendance_date, 'employee':employee}, "name") or None

def get_checkin_details(employee, start, end):
	checkin = frappe.db.sql(""" select time from `tabEmployee Checkin` where employee='{0}' and time>='{1}' and time<='{2}' order by time """.format(employee, start, end))
	return [i[0] for i in checkin]
def get_holiday_list(employee, shift, company):
	holiday = frappe.db.get_value("Shift Type", shift, "holiday_list")
	if not holiday:
		holiday = frappe.db.get_value("Employee", employee, "holiday_list")
	if not holiday:
		holiday = frappe.db.get_value("Company", company, "default_holiday_list")
	if not holiday:
		frappe.throw("Set holiday list to Shift:{0} or Employee:{1} or Company:{2}".format(shift, employee, company))
	return holiday

def get_employee(shift, sync_date):
	return frappe.db.get_all("Shift Assignment", {"shift_type":shift, "start_date":["<=", str(sync_date)], "end_date":[">=", str(sync_date)], "docstatus":1}, "employee")

def get_shifts(from_time, to_time):
	return frappe.db.get_all("Shift Type", {"start_time": [">=", str(from_date)], "start_time": ["<=", str(to_date)]})