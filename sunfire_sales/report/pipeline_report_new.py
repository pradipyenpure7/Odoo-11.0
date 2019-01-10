from odoo import tools
from odoo import api, fields, models


class PipelineReportNew(models.Model):
    _name = "pipeline.report.new"
    _description = "Lead Statistics New"
    _auto = False
    #_order="quote_date desc"
    mnth=fields.Char(string="Month")
    year=fields.Char(string="Year")
    topline=fields.Integer(string="TopLine")
    bottom_line=fields.Integer(string="BottomLine")
    user_id=fields.Char(string="Sales Person")
    oppor_name=fields.Char(string="Oppotunity Name / Quotation")
    oppor_stg=fields.Char(string="Opportunity Stage")
    sale_stage=fields.Char(string="Salews Stage")
    cust=fields.Char(string="Customer")
    pricelist_id=fields.Char(string="Currency")
    vendor=fields.Char(string="Vendor")
    lob=fields.Many2one('line_of_business.info',string="LOB")
    date=fields.Char(string="Lead / Quote Date")
    u_id=fields.Many2one('res.users')
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
                    res_un.name as user_id,
		    u.id as u_id,
                    c.name as oppor_name,
                    o.opportunity_stages as oppor_stg,
                    s.sales_stages as sale_stage,
                    r.name as cust,
                    p.name as pricelist_id, 
                    res_u.name as vendor,
                    l.id as lob,c.create_date::Date as date
                    --ap.id as inside_sales
        from crm_lead c             
        inner join res_partner r on r.id=c.partner_id 
        inner join res_users u on u.id=c.user_id
        inner join res_partner res_un on res_un.id=u.partner_id
        inner join product_pricelist p on p.id=c.crm_pricelist_id
        left join opportunity_stages_info o on o.id=c.opportunity_stages
        left join sales_stages_info s on s.id=c.sales_stages
        left join dr_data_info d on c.id=d.crm_order_dr_id
        left join res_partner res_u on res_u.id=d.oem1
        left join line_of_business_info l on l.id=d.dr_lob
        where c.id not in (select distinct opportunity_id from sale_order where opportunity_id is not null)
        union all 


        select 
        row_number() OVER () as id,
                    to_char(to_timestamp(to_char(a.date_deadline_mnth, '999'), 'MM'), 'Mon') as mnth,
                            a.date_deadline_year as year, 
                            sum(b.price_total), 
                            sum(b.margin),
                            h.name,
			    g.id as u_id, 
                            a.name, 
                            j.opportunity_stages, 
                            k.sales_stages, 
                            f.name, 
                            l.name,
                            split_part(e.complete_name,'/',1),
                            b.line_of_business, 
                            a.create_date::Date as date
                            --a.id, 
        from   sale_order a
        inner join sale_order_line b on a.id=b.order_id
        inner join product_product c on c.id = b.product_id
        inner join product_template d on d.id=c.product_tmpl_id
        inner join product_category e on e.id=d.categ_id
        inner join res_partner f on f.id = a.partner_id
        inner join res_users g on g.id = a.user_id
        inner join res_partner h on h.id = g.partner_id
        inner join product_pricelist l on l.id = a.pricelist_id
        left join line_of_business_info i on i.id = b.line_of_business 
        left join opportunity_stages_info j on j.id = a.opportunity_stages
        left join sales_stages_info k on k.id = a.sales_stages
        where   a.state = 'draft'
        group by split_part(e.complete_name,'/',1), 
        b.line_of_business, a.date_deadline_year, a.name, mnth, 
        f.name, h.name,u_id,a.create_date::Date, j.opportunity_stages, 
        k.sales_stages,l.name)
        """%(self._table))

class PipelineReportDisplay(models.Model):
    _name = "pipeline.report.display"
    _description = "Lead Statistics Display"
    _auto = False
    #_order="quote_date desc"
    mnth=fields.Char(string="Expected Closing (Month)")
    year=fields.Char(string="Expected Closing (Year)")
    topline=fields.Integer(string="TopLine")
    bottom_line=fields.Integer(string="BottomLine")
    user_id=fields.Char(string="Sales Person")
    oppor_name=fields.Char(string="Oppotunity Name / Quotation No.")
    oppor_stg=fields.Char(string="Opportunity Stage")
    sale_stage=fields.Char(string="Sales Stage")
    cust=fields.Char(string="Customer")
    pricelist_id=fields.Char(string="Currency")
    vendor=fields.Char(string="Vendor")
    lob=fields.Many2one('line_of_business.info',string="LOB")
    date=fields.Char(string="Lead / Quotation Date")
    u_id=fields.Many2one('res.users')

    @api.model_cr
    def init(self):
        #self._table = quotation_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW  %s as(
            select row_number() OVER () as id, 
            mnth,year,topline,bottom_line,user_id,u_id,oppor_name,oppor_stg,sale_stage,cust
            ,pricelist_id,vendor,lob,date
            from pipeline_report_new)
        """%(self._table))
