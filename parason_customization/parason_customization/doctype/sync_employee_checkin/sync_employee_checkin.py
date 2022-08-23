# Copyright (c) 2022, Aerele Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pyodbc
from datetime import datetime, timedelta, date

class SyncEmployeeCheckin(Document):
	@frappe.whitelist()
	def add_checkin_data(self):
		if not (self.from_time and self.to_time):
			frappe.throw("From and To Date are mandatory")
		from_time = datetime.strptime(str(self.from_time), "%Y-%m-%d %H:%M:%S")
		to_time = datetime.strptime(str(self.to_time), "%Y-%m-%d %H:%M:%S")
		if from_time > to_time:
			frappe.throw("From Time cannot be greater then To Time")
		if (from_time > datetime.now() or to_time > datetime.now()):
			frappe.throw("From and To Datetime cannot be greater than current time")
		get_checkin_logs(from_time, to_time)
def get_checkin_logs(from_time, to_time):
	server = "192.168.0.48"
	database = "cosec"
	username = "erpnext"
	password = "Erpnext@2022"
	cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
	cursor = cnxn.cursor()
	cursor.execute("""SELECT
				Edatetime,
				CONVERT(VARCHAR(20), UsrRefCode) AS UsrRefCode,
				EVTSeqNo,
				CONVERT(INT, MID) AS MID,
				CONVERT(VARCHAR(20), JobCode) AS JobCode
			FROM
				dbo.Mx_ATDEventTrn
			WHERE
				(Edatetime >= CONVERT(DATETIME, '{0}', 102)) and
				(Edatetime <= CONVERT(DATETIME, '{1}', 102)) """.format(str(from_time), str(to_time)))
	row = cursor.fetchall()
	emp_not_avail = []
	for log in row:
		employee = frappe.db.get_value("Employee", {"attendance_device_id": log[1]}, "name")
		if not employee:
			emp_not_avail.append(log[1])
			continue
		checkin = frappe.db.get_value("Employee Checkin", {"employee": employee, "time": str(log[0])})
		if checkin:
			continue
		doc = frappe.new_doc("Employee Checkin")
		doc.employee = employee
		doc.time = log[0]
		doc.save(ignore_permissions=True)
	frappe.msgprint("Checkin Logs Added")
