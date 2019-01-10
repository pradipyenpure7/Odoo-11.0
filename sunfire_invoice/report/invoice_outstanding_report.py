from odoo import tools
from odoo import api, fields, models


class InvoiceOutstandingReport(models.Model):
    _name = "invoice_outstanding.report"
    _description = "Outstanding Invoice Statistics"
    _auto = False
    _rec_name = 'cust'
    #_order = 'part_id desc'
    opfno=fields.Char(string='OPF No.',readonly=True)
    po_ref=fields.Char(string='Customer PO',readonly=True)
    opf_date=fields.Date(string='OPF Date',readonly=True)
    sam=fields.Many2one('res.users',string='Sales Person',readonly=True)
    podate=fields.Date(string='Customer PO Date',readonly=True)
    inv_name=fields.Char(string='Invoice Reference/Description',readonly=True)
    inv_no=fields.Char(string='Invoice No.',readonly=True)
    inv_state=fields.Char(string='Invoice State',readonly=True)
    total=fields.Float(string='Total Amount',readonly=True)
    date_due=fields.Date(string='Due Date',readonly=True)
    due_amt=fields.Float(string='Due Amount',readonly=True)
    cust=fields.Many2one('res.partner',string='Customer',readonly=True)
    paymnt_term=fields.Char(string='Payment Term',readonly=True)
    term_days=fields.Char(string='Term Days',readonly=True)
    inv_date=fields.Date(string="Invoice Date")
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW  %s as(
            select
            row_number() OVER () as id,
            a.opf_name as opfno,
            a.client_order_ref as po_ref,
            a.confirmation_date as opf_date,
            a.user_id as sam,
            a.po_date as podate,
            b.name inv_name,
            b.date_invoice as inv_date,
            b.number as inv_no,
            b.state as inv_state,
            b.amount_total as total,
            b.date_due,
            b.residual as due_amt,
            b.partner_id as cust,
            c.name paymnt_term,
            d.days as term_days
            from account_invoice b 
            inner join account_payment_term c on b.payment_term_id=c.id
            inner join account_payment_term_line d on d.payment_id=c.id
            inner join sale_order a on a.name = b.origin
            where d.value='balance' and b.residual > 0 and b.date_due > '2018-10-31'
        )  
            """%(self._table))
