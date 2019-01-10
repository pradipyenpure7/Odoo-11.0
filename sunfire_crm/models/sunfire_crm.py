from odoo import api, fields, models,_
from datetime import datetime
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class SunfireCrm(models.Model):
    _inherit = 'crm.lead'
    shrt_name=fields.Char("Short Name",size=150)
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange',required=True, index=True,help="Linked partner (optional). Usually created when converting the lead.")
    priority = fields.Selection(string='Key Deal', selection=[('Yes', 'Yes'), ('No', 'No'),],default='Yes')
    inside_sales=fields.Many2one('approval.info')
    # inside_sales=fields.Selection("inside_sales_vals","Inside Sales")
    planned_revenue = fields.Float('Expected Revenue (TL)', track_visibility='always',compute="sum_plan_rev",store=True)
    bottom_line_revenue=fields.Float('Expected Revenue (BL)', track_visibility='always')
    deal_type=fields.Many2one('deal_type.info')
    
    oem2=fields.Many2one('res.partner',string='Vendor')
    dr_lines=fields.One2many('dr_data.info', 'crm_order_dr_id', string='Order Lines',copy=True, auto_join=True)
    date_deadline_mnth=fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                          (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), 
                          (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')],'Expected closing (Month)')
    date_deadline_year=fields.Selection([(num, str(num)) for num in range(2018, (datetime.now().year)+8 )],'Expected Closing (Year)')
    crm_pricelist_id=fields.Many2one('product.pricelist',string="Revenue Type",required=True)
    opportunity_stages=fields.Many2one('opportunity_stages.info')
    sales_stages=fields.Many2one('sales_stages.info') 
    crm_line=fields.One2many('sale.order','opportunity_id')
    quotation_name=fields.Char(related="crm_line.name",string="Quotation Number")
    oem=fields.Char(string="Vendor",compute='vendor_list')
    deal=fields.Char(string="Deal Type",compute='deal_list')
    lob=fields.Char(string="LOB",compute='lob_list')
    dr_amount=fields.Float(related="dr_lines.dr_amount", string="Amount")
    planned_rev_shrt=fields.Integer('Expected Revenue (TL)', track_visibility='always',compute='new_amt_total')
    bottom_rev_shrt=fields.Integer('Expected Revenue (BL)', track_visibility='always',compute='new_amt_total_bottom',digits=dp.get_precision('Bottom Line'))
    probability=fields.Float(string="Probability (%)",digits=dp.get_precision('Probability'))
    create_date_new=fields.Date(string="Lead Date",compute='new_date_create',store=True)
    write_date_new=fields.Date(string="Lead Date",compute='new_date_write',store=True)
    currency_id = fields.Many2one("res.currency", related='crm_pricelist_id.currency_id', string="Currency", readonly=True)
    vertical=fields.Selection([(1,'1.0 (Hardware, Software)'),(2, '2.0 (PSO, MSO)'),(3,'3.0 (IOT, BI)')],string='Vertical')
    @api.depends('planned_revenue')
    def new_amt_total(self):
        for dt in self:
            if dt.planned_revenue:
                temp = dt.planned_revenue
                dt.planned_rev_shrt=temp
            else:
                dt.amount_total_new=0

    @api.depends('bottom_line_revenue')
    def new_amt_total_bottom(self):
        for dt in self:
            if dt.bottom_line_revenue:
                temp = dt.bottom_line_revenue
                dt.bottom_rev_shrt=temp
            else:
                dt.bottom_rev_shrt=0
    #function to change the format of Date
    @api.depends('write_date')
    def new_date_write(self):
        for dt in self:
            if dt.write_date!=False:
                temp = datetime.strptime(dt.write_date,"%Y-%m-%d %H:%M:%S").date()
                dt.write_date_new=temp
                #print("======>",dt.date_order_new)
            else:
                dt.write_date_new=""

    #function to change the format of Date
    @api.depends('create_date')
    def new_date_create(self):
        lang_obj=self.env['res.lang']
        lang=lang_obj.search([("name","=","English")])
        for dt in self:
            if dt.write_date!=False:
                temp = datetime.strptime(dt.create_date,"%Y-%m-%d %H:%M:%S").date()
                dt.create_date_new=temp
                #print("======>",self.date_order_new)\
            else:
                dt.write_date_new=""
    
    #function concats the distributers(vendor_dr_id) in a list as char
    def vendor_list(self):
        li=[]
        
        for order in self:
            if order.dr_lines:
                oem=""
                for i in order.dr_lines:
                    if i.oem1:
                        oem+=i.oem1.name + '(' + str(int(i.dr_amount)) + ')' + ", "
                        order.oem=oem
                    else:
                        oem+=""
                oem=""

    #function concats the Deal Types(dr_deal_type) in a list as char
    def deal_list(self):
        li=[]
        oem=""
        for order in self:
            if order.dr_lines:
                for i in order.dr_lines:
                    if i.dr_deal_type:
                        oem+=i.dr_deal_type.deal_type + ", "
                        order.deal=oem
                    else:
                        order.deal=""
                oem=""

    #function concats the lob(line_of_business) in a list as char
    def lob_list(self):
        li=[]
        oem=""
        for order in self:
            if order.dr_lines:
                for i in order.dr_lines:
                    if i.dr_lob:
                        oem+=i.dr_lob.line_of_business + ", "
                        order.lob=oem
                    else:
                        order.lob=""
                oem=""

    #function calculates the topline from the amount entered against each vendor in dr tab
    @api.depends("dr_lines.dr_amount")
    def sum_plan_rev(self):
        for order in self:
            order.planned_revenue=0.0
            temp=0.0
            for vals in order.dr_lines:
                if vals.dr_amount:
                    temp+=vals.dr_amount
                    #print("temp====+++++++++>",temp)
                else:
                    order.planned_revenue=0.0        
            order.planned_revenue=temp
            #print("planned_revenue===========>",order.planned_revenue,temp)

    #function for fields.selection but now using the many@one field for dropdown
    # @api.multi
    # def inside_sales_vals(self):
    #     appr_vals=[]
    #     abc=[]
    #     domain={}
    #     approval_obj=self.env['approval.info']
    #     inside_sales_ids=approval_obj.search([('approval_type','=','Inside Sales')])
        #print(inside_sales_ids)
        # for i in inside_sales_ids:
            #print("ids and users====================>",i.id,i.users.name)
        #     appr_vals.append((i.users.id,i.users.name))
        # abc=appr_vals
        # return appr_vals
    def quote_validations(self):
        for order in self:
            if order.vertical==False:
                raise UserError(_("Vertical must be Specified"))
            if order.date_deadline_mnth==False:
                raise UserError(_("Expected Closing Month should not be Empty"))
            if order.date_deadline_year==False:
                raise UserError(_("Expected Closing Year should not be Empty"))
    #Create Quotation with default values
    @api.multi
    def sale_action_quotations_new(self):
        sale_order_obj=self.env['sale.order']
        self.quote_validations()
        so_order= {
                    'opportunity_stages':self.opportunity_stages.id,
                    'sales_stages':self.sales_stages.id,
                    'partner_id':self.partner_id.id,
                    'partner_invoice_id':self.partner_id.id,
                    'partner_shipping_id':self.partner_id.id, 
                    'pricelist_id':self.crm_pricelist_id.id,
                    'opportunity_id':self.id,
                    'shrt_name':self.shrt_name,
                    'date_deadline_mnth':self.date_deadline_mnth,
                    'date_deadline_year':self.date_deadline_year,
                    'vertical':self.vertical,
            }
        sale_order_obj_id=sale_order_obj.create(so_order)
        for i in self:
            if i.dr_lines:
                for ids in i.dr_lines:
                    ids.order_dr_id=sale_order_obj_id.id
            else:
                raise UserError(_("Distributor must be specified in DR Information"))
        view = self.env.ref('sale.view_order_form')
        ctx=dict(self.env.context)
        stage=self.env['crm.stage'].search([('name','=','Quotation')])
        self.stage_id=stage.id
        return {
        'name': 'Quotation',
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'sale.order',
        'res_id':sale_order_obj_id.id,
        'views': [(view.id, 'form')],
        'target': 'new',
        'context': ctx,
    }

   

class crm_dr_info(models.Model):
    _inherit='dr_data.info' 
    
    crm_order_dr_id = fields.Many2one('crm.lead', string='Order DR Reference', ondelete='cascade', index=True, copy=False)
    user_id=fields.Many2one(related="crm_order_dr_id.user_id")
    dr_amount=fields.Float(string="amount")
    dr_lob=fields.Many2one('line_of_business.info',string='Line of Business',required=True)
    dr_deal_type=fields.Many2one('deal_type.info',required=True)
    
    inside_sales=fields.Many2one(related="crm_order_dr_id.inside_sales")
    create_date_new=fields.Date(related="crm_order_dr_id.create_date_new")
    quotation_name=fields.Char(related="crm_order_dr_id.quotation_name")
    partner_id=fields.Many2one(related="crm_order_dr_id.partner_id")
    oem2=fields.Many2one(related="crm_order_dr_id.oem2")
    name=fields.Char(related="crm_order_dr_id.name")
    currency_id=fields.Many2one(related="crm_order_dr_id.currency_id")
    planned_rev_shrt=fields.Integer(related="crm_order_dr_id.planned_rev_shrt")
    bottom_rev_shrt=fields.Integer(related="crm_order_dr_id.bottom_rev_shrt")
    opportunity_stages=fields.Many2one(related="crm_order_dr_id.opportunity_stages")
    sales_stages=fields.Many2one(related="crm_order_dr_id.sales_stages")
    date_deadline_mnth=fields.Selection(related="crm_order_dr_id.date_deadline_mnth")
    date_deadline_year=fields.Selection(related="crm_order_dr_id.date_deadline_year")
    
class stages_info(models.Model):
    _name="stages.info"
    stages_line_id=fields.Many2one('crm.lead',ondelete='cascade', index=True, copy=False)
    sales_stages=fields.Many2one('sales_stages.info')
    opportunity_status=fields.Many2one('opportunity_stages.info')




















    

    
    