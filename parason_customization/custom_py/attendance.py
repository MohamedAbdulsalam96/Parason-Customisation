import frappe
from datetime import datetime, timedelta, date, time


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
		shift_start = datetime.strptime(str(sync_date)+" "+str(shift_start), "%Y-%m-%d %H:%M:%S")
		shift_end = datetime.strptime(str(sync_date)+" "+str(shift_end), "%Y-%m-%d %H:%M:%S")
		margin_start_date = shift_start - timedelta(hours=1)
		margin_end_date = shift_end + timedelta(hours=7)
		employees = get_employee(shift, sync_date)
		for employee in employees:
			create_attendance(employee.employee, sync_date, shift)
	#frappe.msgprint("Attendance is created")

def create_attendance(employee, sync_date, shift=None):
	if not shift:
		shift = get_cur_shift(employee, sync_date)

	shift_start, shift_end = frappe.db.get_value("Shift Type", shift, ["start_time", "end_time"])
	shift_begin = datetime.strptime(str(shift_start), "%H:%M:%S")
	shift_term = datetime.strptime(str(shift_end), "%H:%M:%S")
	shift_duration = (shift_term - shift_begin).seconds
	frappe.errprint(sync_date)
	frappe.errprint(shift_begin.time)
	shift_start = datetime.strptime(str(sync_date)+" "+str(shift_begin.time()), "%Y-%m-%d %H:%M:%S")
	shift_end = shift_start + timedelta(seconds=shift_duration)

	margin_start_date = shift_start - timedelta(hours=1)
	margin_end_date = shift_end + timedelta(hours=7)

	half_day_limit = frappe.db.get_value("Attendance Settings", "Attendance Settings", "half_day_limit")
	full_day_limit = frappe.db.get_value("Attendance Settings", "Attendance Settings", "full_day_limit")
	late_entry_limit = frappe.db.get_value("Attendance Settings", "Attendance Settings", "late_entry_buffer_time")
	overtime_limit = frappe.db.get_value("Attendance Settings", "Attendance Settings", "overtime_limit")

	if not half_day_limit:
		frappe.throw("Set Half day Limit in {0}".format(frappe.utils.get_link_to_form("Attendance Settings")))

	if not full_day_limit:
                frappe.throw("Set Full day Limit in {0}".format(frappe.utils.get_link_to_form("Attendance Settings") ))

	if not late_entry_limit:
                frappe.throw("Set Late Entry Limit in {0}".format(frappe.utils.get_link_to_form("Attendance Settings") ))

	if not overtime_limit:
                frappe.throw("Set Overtime Limit in {0}".format(frappe.utils.get_link_to_form("Attendance Settings") ))

	half_day_limit = int(half_day_limit) / 60 / 60
	full_day_limit = int(full_day_limit) / 60 / 60
	late_entry_limit = int(late_entry_limit) / 60
	overtime_limit = int(overtime_limit) / 60

	duplicate = check_duplication(str(sync_date), employee)
	if duplicate:
		doc = frappe.get_doc("Attendance", duplicate)
	else:
		doc = frappe.new_doc("Attendance")
	company = frappe.db.get_value("Employee", employee, "company")
	holiday_list = get_holiday_list(employee, shift, company)
	checkin = get_checkin_details(employee, margin_start_date, margin_end_date)
	if len(checkin) in [0, 1]:
		leave = frappe.db.get_value("Leave Application", {"employee":employee, "from_date":[">=", str(sync_date)],
			"to_date":["<=", str(sync_date)], "docstatus": 1})
		is_holiday = frappe.get_value("Holiday", {"holiday_date": str(sync_date), "parent":holiday_list})
		doc.employee = employee
		doc.shift = shift
		doc.check_in_time = checkin[0] if len(checkin) else "00:00:00"
		doc.check_out_time = "00:00:00"
		doc.attendance_date = sync_date
		doc.status = "On Leave"
		if is_holiday:
			week_off = frappe.get_value("Holiday", is_holiday, "weekly_off")
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
	else:
		check_in = checkin
		checkin = check_in[0] #datetime.strptime(checkin[0].split(".")[0], "%Y-%m-%d %H:%M:%S")
		checkout = check_in[-1] #datetime.strptime(checkin[-1].split(".")[0], "%Y-%m-%d %H:%M:%S")

		short_leave_req = frappe.db.get_value("Short Leave Request", {"from_time": [">=", str(sync_date)], "to_time":["<=", str(sync_date+timedelta(days=1))]})
		if short_leave_req:
			short_leave = frappe.get_doc("Short Leave Request", short_leave_req)
			begin_interval = short_leave.from_time - shift_start
			end_interval = shift_end - short_leave.to_time
			if begin_interval < end_interval and checkin > short_leave.from_time:
				checkin = short_leave.from_time
			elif begin_interval > end_interval and checkout < short_leave.to_time:
				checkout = short_leave.to_time

		#in_time = datetime.combine(date.min, checkin.time()) - datetime.min
		#shift_in_time = datetime.combine(date.min, shift_start.time()) - datetime.min
		#in_time_delay = (in_time - shift_in_time).seconds / 60
		in_time_delay = 0
		if shift_start < checkin:
			in_time_delay = (checkin - shift_start).seconds / 60

		#out_time = datetime.combine(date.min, checkout.time()) - datetime.min
		#shift_out_time = datetime.combine(date.min, shift_end.time()) - datetime.min
		#over_time = (out_time - shift_out_time).seconds / 60
		over_time = 0
		if shift_end < checkout:
			over_time = (checkout - shift_end).seconds / 60

		doc.employee = employee
		doc.shift = shift
		doc.check_in_time = checkin
		doc.check_out_time = checkout
		doc.attendance_date = sync_date
		duration = checkout - checkin
		duration = duration.seconds / 60 / 60
		doc.status = "Present"
		is_half_day = False
		if in_time_delay > late_entry_limit:
			is_half_day = True
			doc.late_entry = 1
		if duration < half_day_limit and duration >= half_day_limit:
			is_half_day = True
		if duration < half_day_limit:
			doc.status = "Absent"
		if is_half_day:
			leave_doc = frappe.new_doc("Leave Application")
			leave_doc.employee = employee
			leave_doc.from_date = sync_date
			leave_doc.to_date = sync_date
			leave_doc.half_day = 1
			leave_approver = frappe.db.get_value("Employee", employee, "leave_approver")
			if not leave_approver:
				frappe.throw("Set Leave Approver for Employee:{0}".format(employee))
			leave_doc.leave_approver = leave_approver
			leave_doc.company = company
			leave_doc.save(ignore_permissions=True)
			leave_doc.submit()
		if frappe.db.get_value("Employee", employee, "allow_over_time") and over_time > 0 and over_time > overtime_limit:
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
	if not duplicate:
		doc.submit()


def check_duplication(attendance_date, employee):
	return frappe.db.exists("Attendance", {'attendance_date':attendance_date, 'employee':employee, "docstatus":1})


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

def get_cur_shift(employee, shift_date):
	shift = frappe.db.get_value("Shift Assignment", {"start_date": ["<=", shift_date], "end_date": [">=", shift_date], "docstatus":1, "status":"Active"}, "shift_type")
	if not shift:
		shift = frappe.db.get_value("Shift Assignment", {"start_date": [">=", shift_date], "docstatus":1, "status":"Active"}, "shift_type")
	return shift
