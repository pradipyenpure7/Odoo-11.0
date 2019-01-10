from odoo import tools
from odoo import api, fields, models


class QuotationReport(models.Model):
    _name = "quotation.report"
    _description = "Quotation Statistics"
    _auto = False
    _rec_name = 'date_order'
    #_order = 'part_id desc'
    
    name = fields.Char('Order Reference', readonly=True)
    date_order = fields.Date('Quotation Date', readonly=True)
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    top_price=fields.Integer(string="Top Line",readonly=True)
    part_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    user_id=fields.Many2one('res.users','Sales Person')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', readonly=True)
    currency_id=fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True)
    btm_line=fields.Integer("Bottom line",readonly=True)
    lob=fields.Many2one('line_of_business.info',string="LOB",readonly=True)
    product_catagory=fields.Char("Vendor",readonly=True)

    @api.model_cr
    def init(self):
        #self._table = quotation_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW  %s as(
            select 
            min(l.id) AS id,
            case when s.date_order::Date is null Then s.date_revise::Date
            else s.date_order::Date end AS date_order,
            s.name AS name, 
            split_part(c.complete_name,'/',1) AS product_catagory,
            p.categ_id AS categ_id,
            l.line_of_business AS lob,
            sum(price_subtotal) as top_price,
            sum(l.margin) AS btm_line,
            a.id AS user_id,
            g.id AS part_id,
            j.id AS pricelist_id
            from 
            sale_order s 
            inner join sale_order_line l 
                on s.id=l.order_id
            inner join product_pricelist j
                on j.id=s.pricelist_id
            inner join res_users a
                on a.id=s.user_id
            inner join res_partner g
                on g.id=s.partner_id
            inner join product_template p 
                on p.id=l.product_id
            inner join product_category c 
                on c.id=p.categ_id
            where s.state='draft'
            group by  
                s.name ,split_part(c.complete_name,'/',1),p.categ_id,l.line_of_business,date_order,j.id,
                part_id,a.id, s.date_revise
            )  
            """%(self._table))
class QuotationReportProforma(models.AbstractModel):
    _name = 'report.sale.quotation_report'

    @api.multi
    def get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
            'proforma': True
        }
