from odoo import tools
from odoo import api, fields, models


class PipelineReport(models.Model):
    _name = "pipeline.report"
    _description = "Lead Statistics"
    _auto = False
    _order="quote_date desc"
    #_rec_name = 'date_order'
    # id=fields.Integer()
    mnth=fields.Char(string='Expected Closing (Month)')
    year=fields.Char(string="Expeected Closing (Year)")
    topline=fields.Integer(string="Expected Revenue(TL)")
    bottom_line=fields.Integer(string="Expected Revenue(BL)")
    user_id=fields.Many2one('res.users',string="Sales Person")
    oppor_name=fields.Char(string="Opportunity")
    oppor_stg=fields.Many2one('opportunity_stages.info',string="Opportunity Stage")
    sale_stage=fields.Many2one('sales_stages.info',string="Sales Stage")
    cust=fields.Many2one('res.partner',string="Customer")
    pricelist_id=fields.Many2one('product.pricelist',string="Price List")
    currency_id=fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True)
    vendor=fields.Many2one('res.partner',string="Vendor")
    inside_sales=fields.Many2one('approval.info',string="Inside Sales")
    quote_date=fields.Date(string="Lead / Quotation Date")
    quote_name=fields.Char(string="Quotation No.")
    lob=fields.Many2one('line_of_business.info',string="LOB")


    @api.model_cr
    def init(self):
        #self._table = quotation_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW  %s as(
        select  
            row_number() OVER () as id,to_char(to_timestamp(to_char(c.date_deadline_mnth, '999'), 'MM'), 'Mon') as mnth,
            c.date_deadline_year as year,
            c.planned_revenue as topline,
            c.bottom_line_revenue as bottom_line,
            u.id as user_id,
            c.name as oppor_name,
            c.opportunity_stages as oppor_stg,
            c.sales_stages as sale_stage,
            c.partner_id as cust,
            c.crm_pricelist_id as pricelist_id,
            d.oem1 as vendor,
            l.id as lob,ap.id as inside_sales,
            case when so.create_date is null then c.create_date::Date 
            else so.create_date::Date end as quote_date,
            so.name as quote_name
             
            from crm_lead c 
            
            inner join res_users u on u.id=c.user_id
            inner join res_partner r on r.id=c.partner_id 
            inner join product_pricelist p on p.id=c.crm_pricelist_id
            left join sale_order so on so.opportunity_id=c.id
            left join opportunity_stages_info o on o.id=c.opportunity_stages
            left join sales_stages_info s on s.id=c.sales_stages
            left join approval_info ap on ap.id=c.inside_sales
            left join dr_data_info d on c.id=d.crm_order_dr_id
            left join line_of_business_info l on l.id=d.dr_lob --where so.state='draft'
            group by 
            mnth,year,topline,bottom_line,u.id,oppor_name,oppor_stg,sale_stage,cust,c.crm_pricelist_id,
            d.oem1,ap.id,quote_date,quote_name,l.id
            order by quote_date desc
            )
            """%(self._table))
