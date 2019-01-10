from odoo import tools
from odoo import api, fields, models


class TimesheetReport(models.Model):
    _name = "timesheet.report"
    _description = "Timesheet Statistics"
    _auto = False
    #_rec_name = 'date_order'
    #_order = 'part_id desc'
    
    categ = fields.Char(string="Category")
    create_date = fields.Date('Timesheet Date')
    sub_category=fields.Char(string="Subcategory")
    partner_name = fields.Char(string='Customer')
    poa = fields.Char(string='POA')
    outcome = fields.Char(string='Outcome')
    time = fields.Float(string='Timespent')
    user_id=fields.Many2one("res.users")
    function=fields.Char(string="Function")
    @api.model_cr
    def init(self):
        #self._table = quotation_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW  %s as(
            select
            row_number() OVER () as id,
            a.create_uid as user_id,
            e.approval_type as function, 
            a.timesheet_date as create_date,
            c.category as categ,
            d.sub_category,
            p.name as partner_name,
            b.poa as poa,
            b.outcome as outcome,
            b.timespent as time
            from 
            sunfire_timesheet as a 
            inner join sunfire_timesheet_line b 
                on a.id=b.timesheet_id
            left join res_partner p on b.customer=p.id
            left join category_info c on b.category=c.id
            left join sub_category_info d on b.sub_category=d.id
            left join approval_types_info e on b.role_type=e.id
            )  
            """%(self._table))

