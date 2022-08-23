// Copyright (c) 2022, Aerele Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Overtime Request', {
	refresh: function(frm) {
		frm.set_query('employee', function(doc) {
			return {
				filters: {
				    "allow_over_time": 1
				}
			};
		});
	}
});
