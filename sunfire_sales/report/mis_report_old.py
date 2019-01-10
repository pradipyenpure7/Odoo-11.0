from odoo import tools
from odoo import api, fields, models


class MisReport(models.Model):
	_name = "mis.report"
	_description = "MIS Report"
	_auto = False
	#_rec_name = 'confirmation_date'
	id=fields.Integer()
	user_id=fields.Many2one('res.users',string="Sales Person")
	customer_name=fields.Many2one('res.partner',string='Customer')
	opf_name=fields.Char(string="OPF Number")
	purchase_val_stp=fields.Float('Purchase Value')
	btm_line_margin_in=fields.Float(string='Bottom Line In')
	top_line_in_ctp=fields.Float(string='Top Line In')
	lob=fields.Many2one('line_of_business.info',string='LOB')
	purchase_nego=fields.Float(string='Purchase Value Negotiated')
	toplineoutinv=fields.Float(string='Top Line Out')
	act_btm_line_margin_in=fields.Float(string='Actual Bottom Line In')
	btm_line_out=fields.Float(string='Bottom Line Out')
	quat=fields.Char('SY Quarter In')
	inv_quat=fields.Char("SY Quarter Out")
	fin_yr=fields.Char(string='Financial Year')
	sale_yr=fields.Char(string='Sale Year')
	in_mnth=fields.Char(string='In Month')
	inv_no=fields.Char(string='Invoice Number')
	inv_date=fields.Date(string='Invoice Date')
	out_mnth=fields.Char(string='Out Month')
	product_catagory=fields.Char(string='Vendor')
	cust_type=fields.Many2one('cust.type',string='Customer Type')
	location=fields.Char(string='Billing Location')
	pricelist_id = fields.Many2one('product.pricelist', 'Price List')
	currency_id=fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True)
	stata=fields.Char(string='Sales In / Out')
	
	@api.model_cr
	def init(self):
		#self._table = quotation_report
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW  %s as(
				select 
				row_number() OVER () as id,
				CASE
				when EXTRACT(month from ord.confirmation_date) BETWEEN 11 AND 1 THEN 'Q1'
				when EXTRACT(month from ord.confirmation_date) BETWEEN 2 AND 4 THEN 'Q2'
				when EXTRACT(month from ord.confirmation_date) BETWEEN 5 AND 7 THEN 'Q3'
				when EXTRACT(month from ord.confirmation_date) BETWEEN 7 AND 10 THEN 'Q4' END as quat, 
				u.id as user_id,
				res.id as customer_name,
				ord.opf_name as opf_name,
				sl.line_of_business as lob,
				trim(split_part(c.complete_name,'/',1)) AS product_catagory,
				sl.purchase_price*sl.product_uom_qty as purchase_val_stp,
				sl.margin_value*sl.product_uom_qty as btm_line_margin_in,
				sl.price_unit* sl.product_uom_qty as top_line_in_ctp,
				case 
				when pl.purchase_price*pl.product_qty is null then 0.00
				else pl.purchase_price*pl.product_qty end as purchase_nego,
				case 
				when (sl.price_unit*sl.product_uom_qty)-(pl.purchase_price*pl.product_qty) is null then 0.00
				else (sl.price_unit*sl.product_uom_qty)-(pl.purchase_price*pl.product_qty) end as act_btm_line_margin_in,
				case 
				when al.quantity*al.price_unit is null then 0.00
				else al.quantity*al.price_unit end as toplineoutinv,
				case
				when (al.quantity*al.price_unit)-(sl.purchase_price*sl.product_uom_qty) is null then 0.00
				else (al.quantity*al.price_unit)-(sl.purchase_price*sl.product_uom_qty) end as btm_line_out,
				case when to_char(ord.confirmation_date,'mm')::int>=11 then 'SY'||to_char(ord.confirmation_date,'YY')::int||'-'||to_char(ord.confirmation_date,'YY')::int+1
				else 'SY'||to_char(ord.confirmation_date,'YY')::int-1||'-'||to_char(ord.confirmation_date,'YY')::int end as sale_yr,
				case when to_char(ord.confirmation_date,'mm')::int>=4 then 'FY'||to_char(ord.confirmation_date,'YY')::int||'-'||to_char(ord.confirmation_date,'YY')::int+1
				else 'FY'||to_char(ord.confirmation_date,'YY')::int-1||'-'||to_char(ord.confirmation_date,'YY')::int end as fin_yr,
				TO_CHAR(ord.confirmation_date :: DATE,'MON ,YY' ) as in_mnth,
				CASE
				when EXTRACT(month from ac.date_invoice) BETWEEN 11 AND 1 THEN 'Q1'
				when EXTRACT(month from ac.date_invoice) BETWEEN 2 AND 4 THEN 'Q2'
				when EXTRACT(month from ac.date_invoice) BETWEEN 5 AND 7 THEN 'Q3'
				when EXTRACT(month from ac.date_invoice) BETWEEN 7 AND 10 THEN 'Q4' END as inv_quat,
				ac.number as inv_no,
				ac.date_invoice::Date as inv_date,
				to_char(ac.date_invoice::Date,'MON ,YY') as out_mnth,
				res.cust_type as cust_type,
				ord.billing_location as location,
				j.id AS pricelist_id,
				CASE 
				when ac.number is null then 'In'
				Else 'Out'
				End as stata
				from sale_order_line sl 
				inner join res_partner res on sl.order_partner_id=res.id
				inner join cust_type ct on ct.id = res.cust_type
				inner join res_users u on u.id=sl.salesman_id
				inner join sale_order ord on ord.id=sl.order_id
				inner join product_pricelist j on j.id=ord.pricelist_id
				inner join product_template t on t.id=sl.product_id
				inner join product_category c on c.id=t.categ_id
				left join purchase_order_line pl on pl.saleorder_line_id=sl.id 
				left join purchase_order p on p.id=pl.order_id
				left join account_invoice ac on ac.origin=ord.name
				left join account_invoice_line al on al.invoice_id=ac.id and al.product_id=sl.product_id 
				where ord.state in ('done','sale')
				)
		"""%(self._table))

class MisNewReport(models.Model):
	_name="mis.new.report"
	_description="MIS report new"
	_auto=False
	user_id=fields.Many2one('res.users',string="Sales Person")
	customer_name=fields.Many2one('res.partner',string='Customer')
	opf_name=fields.Char(string="OPF Number")
	purchase_val_stp=fields.Float('Purchase Value')
	btm_line_margin_in=fields.Float(string='Bottom Line In')
	top_line_in_ctp=fields.Float(string='Top Line In')
	lob=fields.Many2one('line_of_business.info',string='LOB')
	purchase_nego=fields.Float(string='Purchase Value Negotiated')
	toplineoutinv=fields.Float(string='Top Line Out')
	act_btm_line_margin_in=fields.Float(string='Actual Bottom Line In')
	btm_line_out=fields.Float(string='Bottom Line Out')
	quat=fields.Char('SY Quarter In')
	inv_quat=fields.Char("SY Quarter Out")
	fin_yr=fields.Char(string='Financial Year')
	sale_yr=fields.Char(string='Sale Year')
	in_mnth=fields.Char(string='In Month')
	inv_no=fields.Char(string='Invoice Number')
	inv_date=fields.Date(string='Invoice Date')
	out_mnth=fields.Char(string='Out Month')
	product_catagory=fields.Char(string='Vendor')
	cust_type=fields.Many2one('cust.type',string='Customer Type')
	location=fields.Char(string='Billing Location')
	pricelist_id = fields.Many2one('product.pricelist', 'Price List')
	currency_id=fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True)
	stata=fields.Char(string='Sales In / Out')
	@api.model_cr
	def init(self):
		tools.drop_view_if_exists(self.env.cr,self._table)
		self.env.cr.execute(""" CREATE or REPLACE VIEW %s as(
			select row_number() OVER () as id,user_id,customer_name,opf_name,
			sum(purchase_val_stp) as purchase_val_stp,sum(btm_line_margin_in) as btm_line_margin_in,
			sum(top_line_in_ctp) as top_line_in_ctp,lob,
			sum(purchase_nego) as purchase_nego,sum(toplineoutinv) as toplineoutinv,sum(act_btm_line_margin_in) as act_btm_line_margin_in,
			sum(btm_line_out) as btm_line_out,quat,inv_quat,fin_yr,sale_yr,in_mnth,inv_no,inv_date
			,out_mnth,product_catagory,cust_type,location,pricelist_id,stata
			from mis_report
			group by 
			user_id,customer_name,opf_name,lob,quat,inv_quat,fin_yr,sale_yr,in_mnth,inv_no,inv_date
			,out_mnth,product_catagory,cust_type,location,pricelist_id,stata
		) """%(self._table))




		# --select 
		# 		--row_number() OVER () as id,ord.confirmation_date::Date as confirmation_date,
		# 		--CASE
		# 		--when EXTRACT(month from ord.confirmation_date) BETWEEN 11 AND 1 THEN 'Q1'
		# 		--when EXTRACT(month from ord.confirmation_date) BETWEEN 2 AND 4 THEN 'Q2'
		# 		--when EXTRACT(month from ord.confirmation_date) BETWEEN 5 AND 7 THEN 'Q3'
		# 		--when EXTRACT(month from ord.confirmation_date) BETWEEN 7 AND 10 THEN 'Q4' END as quat, 
		# 		--ord.user_id as user_id,
		# 		--ord.partner_id as customer_name,
		# 		--ord.opf_name as opf_name,
		# 		--sl.line_of_business as lob,
		# 		--trim(split_part(c.complete_name,'/',1)) AS product_catagory,
		# 		--sum(sl.purchase_price*sl.product_uom_qty) as purchase_val_stp,
		# 		--sum(sl.margin_value*sl.product_uom_qty) as btm_line_margin_in,
		# 		--sum(sl.price_unit* sl.product_uom_qty ) as top_line_in_ctp,
		# 		--case 
		# 		--when sum(pl.purchase_price*pl.product_qty) is null then 0.00
		# 		--else sum(pl.purchase_price*pl.product_qty) end as purchase_nego,
		# 		--case 
		# 		--when sum(sl.price_unit*sl.product_uom_qty)-sum(pl.purchase_price*pl.product_qty) is null then 0.00
		# 		--else sum(sl.price_unit*sl.product_uom_qty)-sum(pl.purchase_price*pl.product_qty) end as act_btm_line_margin_in,
		# 		--case 
		# 		--when sum(al.quantity*al.price_unit) is null then 0.00
		# 		--else sum(al.quantity*al.price_unit) end as toplineoutinv,
		# 		--case
		# 		--when sum(al.quantity*al.price_unit)-sum(sl.purchase_price*sl.product_uom_qty) is null then 0.00
		# 		--else sum(al.quantity*al.price_unit)-sum(sl.purchase_price*sl.product_uom_qty) end as btm_line_out,
		# 		--case when to_char(ord.confirmation_date,'mm')::int>=11 then 'SY'||to_char(ord.confirmation_date,'YY')::int||'-'||to_char(ord.confirmation_date,'YY')::int+1
		# 		--else 'SY'||to_char(ord.confirmation_date,'YY')::int-1||'-'||to_char(ord.confirmation_date,'YY')::int end as sale_yr,
		# 		--case when to_char(ord.confirmation_date,'mm')::int>=4 then 'FY'||to_char(ord.confirmation_date,'YY')::int||'-'||to_char(ord.confirmation_date,'YY')::int+1
		# 		--else 'FY'||to_char(ord.confirmation_date,'YY')::int-1||'-'||to_char(ord.confirmation_date,'YY')::int end as fin_yr,
		# 		--TO_CHAR(ord.confirmation_date :: DATE,'MON ,YY' ) as in_mnth,
		# 		--CASE
		# 		--when EXTRACT(month from ac.date_invoice) BETWEEN 11 AND 1 THEN 'Q1'
		# 		--when EXTRACT(month from ac.date_invoice) BETWEEN 2 AND 4 THEN 'Q2'
		# 		--when EXTRACT(month from ac.date_invoice) BETWEEN 5 AND 7 THEN 'Q3'
		# 		--when EXTRACT(month from ac.date_invoice) BETWEEN 7 AND 10 THEN 'Q4' END as inv_quat,
		# 		--ac.number as inv_no,
		# 		--ac.date_invoice::Date as inv_date,
		# 		--to_char(ac.date_invoice::Date,'MON ,YY') as out_mnth,
		# 		--res.cust_type as cust_type,
		# 		--ord.billing_location as location,
		# 		--ord.pricelist_id AS pricelist_id,
		# 		--CASE 
		# 		--when ac.number is null then 'In'
		# 		--Else 'Out'
		# 		--End as stata
		# 		--from sale_order_line sl
		# 		--inner join sale_order ord on ord.id=sl.order_id
		# 		--inner join res_partner res on ord.partner_id=res.id
		# 		--inner join cust_type ct on ct.id = res.cust_type
		# 		--inner join res_users u on u.id=ord.user_id
		# 		--inner join res_partner res_u on res_u.id=u.partner_id
		# 		--inner join product_pricelist j on j.id=ord.pricelist_id
		# 		--inner join product_product pro on pro.id=sl.product_id
		# 		--inner join product_template t on t.id=pro.product_tmpl_id
		# 		--inner join product_category c on c.id=t.categ_id
		# 		--left join purchase_order p on p.origin=ord.name
		# 		--left join purchase_order_line pl on pl.order_id=p.id and pl.saleorder_line_id=sl.id 
		# 		--left join account_invoice ac on ac.origin=ord.name
		# 		--left join account_invoice_line al on al.invoice_id=ac.id 
		# 		--where ord.state in ('done','sale')
		# 		--group by 
		# 		--ord.user_id,ord.partner_id,ord.opf_name,sl.line_of_business,quat,inv_quat,fin_yr,sale_yr,in_mnth,ac.number,ac.date_invoice::Date
		# 		--,out_mnth,trim(split_part(c.complete_name,'/',1)),res.cust_type,ord.billing_location,ord.pricelist_id,stata,ord.confirmation_date 