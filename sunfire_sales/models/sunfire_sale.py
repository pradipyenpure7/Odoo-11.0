from odoo import api,fields,models, _
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
from odoo.exceptions import UserError
import smtplib
from datetime import datetime
from ftplib import FTP
from odoo.addons import decimal_precision as dp

#Model Group Code 
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    # model_group_code = fields.Char('Model Group Code')
    #l10n_in_hsn_code = fields.Char(string="HSN/SAC Code", help="Harmonized System Nomenclature/Services Accounting Code")
    
#Extra fields added to SaleOrderLine 
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    i_type = fields.Selection(related='product_id.type',string='Product Type')
    desc_name=fields.Text(related='product_id.description_sale',string='Description')
    # model_group_code = fields.Char(related='product_id.model_group_code',string='Model Group Code')
    categ_id = fields.Many2one(related='product_id.categ_id',string='Product Category')
    l10n_in_hsn_code = fields.Char(related='product_id.l10n_in_hsn_code',string="HSN Code")
    dr_done = fields.Selection([('DR Done', 'DR Done'), ('DR Not Done', 'DR Not Done'),('DR Not Required','DR Not Required')], 'DR Done')
    dr_status = fields.Selection([('Accepted', 'Accepted'), ('Rejected', 'Rejected')], 'DR Status')
    dr_remark = fields.Char('DR Number')
    dr_date = fields.Char('DR Date')
    up_sell=fields.Selection([('No','No'),('Yes','Yes')],'Up Sell',default='No') 
    margin_type = fields.Selection([('Fixed', '₹'), ('Percentage', '%')], 'Margin Type')
    margin_value = fields.Float('Margin Amount')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=False)
    line_of_business=fields.Many2one('line_of_business.info',string='Line of Business')
    product_serial_no = fields.Char(string='product_serial_no')
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'))
    total_stp=fields.Float('Subtotal STP',compute='_amount_stp',readonly=True)
    deal_type_sol=fields.Many2one('deal_type.info',string="Deal Type")
    
    @api.depends('product_uom_qty','purchase_price')
    def _amount_stp(self):
        for line in self:
            if line.purchase_price:
                #print("Here")
                line.total_stp=line.purchase_price*line.product_uom_qty
                #print('line.total_stp',line.total_stp)
    
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            #print("onchange prod uom ############")
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            #print("onchange prod uom ############2",self.price_unit)
            #self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
            #print("onchange prod uom ############23",self.price_unit)
    # ____________-------Margin Calculations------------__________________#
    @api.onchange('margin_value','margin_type','purchase_price','product_uom_qty')
    def _my_compute_margin(self):
        #print("I m here")
        for line in self:
            mt=line.margin_type
            if mt=='Percentage':
                line.price_unit=(line.purchase_price + (line.purchase_price * (line.margin_value/100)))
            else:
                line.update({
                'price_unit':line.purchase_price + line.margin_value
                })
    #_______________-------list for values top be updated------______________#
    def _get_protected_fields(self):
        return [
            'product_id', 'name', 'price_unit', 'product_uom', 'product_uom_qty',
            'tax_id', 'analytic_tag_ids','l10n_in_hsn_code'
        ]
    @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit', 'price_subtotal')
    def _product_margin(self):
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            price = line.purchase_price
            #if not price:
                #from_cur = line.env.user.company_id.currency_id.with_context(date=line.order_id.date_order)
                #print("from_cur========>",from_cur)
                #price = from_cur.compute(line.product_id.standard_price, currency, round=False)
                #print("price,std_price,currency========>",price,line.product_id.standard_price,currency,line.product_id,line.product_id.product_tmpl_id)
            line.margin = currency.round(line.price_subtotal - (price * line.product_uom_qty))
            #print("Margin,price_subtotal=======>",line.margin,line.price_subtotal)
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    
    
    
    
    
    #_order = 'confirmation_date,date_order desc'
    _sql_constraints = [ ('unique_opportunity', 'unique(opportunity_id)', 'Quotation exists')	]
    date_order_new=fields.Date("Quotation Date",compute='new_date_order',store=True)
    confirmation_date_new=fields.Date("OPF Date",compute='new_date_confirmation',store=True)
    write_date_new=fields.Date("Last Updated Date",compute='new_date_write',store=True)
    shrt_name=fields.Char("Short Name",size=150)
    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    opportunity_stages=fields.Many2one('opportunity_stages.info')
    sales_stages=fields.Many2one('sales_stages.info')
    installation_terms=fields.Many2one('installation_terms.info')
    delivery_terms = fields.Many2one('delivery_term.info','Delivery Term')    
    tax_grp = fields.Many2one('account.tax',string="Tax Group")
    transport_modes = fields.Many2one('transport_mode.info',string="Transport Modes")
    validity_dt=fields.Char()
    po_to_be_placed=fields.Many2one('res.partner',string="PO to be Placed")
    po_detail_address=fields.Many2one('res.partner',string="PO addresses",help="Contact Person ")
    addr=fields.Text("Address",readonly=True)
    pre_sale_engaged = fields.Selection([('NA','NA'),('Niranjan Subhash Ghodke','Niranjan Subhash Ghodke'),('Shivaji  Ningappa Dhanagar','Shivaji  Ningappa Dhanagar'),('Ashok Nivrutti Gavhane','Ashok Nivrutti Gavhane'),('Balkrushna Vasudev Tambe','Balkrushna Vasudev Tambe'),('Rajendra Gajendra Raut','Rajendra Gajendra Raut'),('Jitesh Shantaram Mahajan','Jitesh Shantaram Mahajan')])
    billing_location=fields.Char("Billing Location")
    invoice_advice=fields.Char("Invoice Advice")
    po_advice=fields.Char("PO Advice")
    vendor_id=fields.Many2one("res.partner",string="Billing from")
    concern_person=fields.Many2one("res.partner")
    concern_email=fields.Char()
    concern_mobile=fields.Char()
    warranty=fields.Many2one('warranty_information.info','Warranty')
    partner_id = fields.Many2one('res.partner', string='Customer',required=True, change_default=True, index=True, track_visibility='always')
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', help="Invoice address for current sales order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address',help="Delivery address for current sales order.")
    partner_invoice_Add=fields.Text("Detail Address",readonly=True)
    partner_shipping_Add=fields.Text("Detail Address",readonly=True)
    opf_name = fields.Char('OPF Number')
    order_dr_line = fields.One2many('dr_data.info', 'order_dr_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    revise_quote=fields.Selection([('yes','Yes'),('no','No')],'Revise Quotation')
    revision_no=fields.Integer(default=0)
    revision_name=fields.Char()
    order_approve_line=fields.One2many("approval_tab.info","order_approve_id", states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    order_upload_line=fields.One2many("upload_tab.info","order_upload_id")
    amount_stp=fields.Monetary(string='Total STP', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    approve_flag=fields.Boolean(default=True)
    oem=fields.Char(string="Vendor",compute='vendor_list')
    amount_total_new=fields.Integer(string="Total",compute='new_amt_total')
    lob=fields.Char(string="LOB",compute='lob_list')
    cancel_opf_desc=fields.Text(string='OPF Cancelation description')
    date_revise=fields.Date(string="Last Quote date")
    po_date=fields.Date(string="PO Date")
    date_deadline_mnth = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                          (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), 
                          (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')],'Expected closing (Month)')
    date_deadline_year = fields.Selection([(num, str(num)) for num in range(2018, (datetime.now().year)+8 )],'Expected Closing (Year)')
    vertical=fields.Selection([(1,'1.0 (Hardware, Software)'),(2, '2.0 (PSO, MSO)'),(3,'3.0 (IOT, BI)')],string='Vertical')
    sale_yr=fields.Char('  Sale Year  ',compute='get_sale_year')
    financial_yr=fields.Char('Financial Year',compute='get_financial_year')
    
    # 08/01/2019 Pradip  margin_percentage_calculate              
    margin_per=fields.Char(string="Margin (%)",compute='margin_percentage_calculate',store=True)
    @api.depends('amount_untaxed','margin')
    def margin_percentage_calculate(self):
        for i in self:
           # if i.margin and i.amount_untaxed:
             print("===================margin===================",i.margin,"=====",i.amount_untaxed)
             margin_per=(i.margin/i.amount_untaxed)*100
#              i.margin_per=str('(')+str(round(margin_per))+str('%)')
             i.margin_per=round(margin_per)
             print("i.margin_per=================",i.margin_per)

    #This function overrides _rec_name
    @api.multi
    def name_get(self):
        res=[]
        opf_name=""
        for order in self:
            if order.name:
                name=order.name
            if order.opf_name:
                opf_name=order.opf_name
            else:
                opf_name=""
            res.append((order.id,opf_name+' '+name))
        return res
    #Calculates the financial year
    @api.depends('create_date')
    def get_financial_year(self):
        for order in self:
            if order.create_date:
                dt=datetime.strptime(order.create_date,"%Y-%m-%d %H:%M:%S").date()
                if dt.month>3:
                    nxt_yr=datetime.strftime(dt,"%y")
                    nxt_yr=int(nxt_yr)+1
                    fy=datetime.strftime(dt,"FY %y-"+str(nxt_yr))
                    order.financial_yr= fy
                    print("Nxt==========>",order.financial_yr)
                else:
                    before_yr=datetime.strftime(dt,"%y")
                    before_yr=int(before_yr)-1
                    fy=datetime.strftime(dt,"FY "+str(before_yr)+"-"+"%y")
                    order.financial_yr= fy
                    print("Before",order.financial_yr)    
    #Calculates the Sale year
    @api.depends('create_date')
    def get_sale_year(self):
        for order in self:    
            if order.create_date:
                dt=datetime.strptime(order.create_date,"%Y-%m-%d %H:%M:%S").date()
                if dt.month>10:
                    nxt_yr=datetime.strftime(dt,"%y")
                    nxt_yr=int(nxt_yr)+1
                    sy=datetime.strftime(dt,"SY %y-"+str(nxt_yr))
                    order.sale_yr= sy
                    print("Nxt==========>",order.sale_yr)
                else:
                    before_yr=datetime.strftime(dt,"%y")
                    before_yr=int(before_yr)-1
                    sy=datetime.strftime(dt,"SY "+str(before_yr)+"-"+"%y")
                    order.sale_yr=sy
                    print("Before",order.sale_yr)    
    #Calculates Custom names for the field state
    def cal_new_status(self):
        for order in self:
            if order.state=="sale" and order.approve_flag==True:
                order.new_status="Validated"
            elif order.state=="sale" and order.approve_flag==False:
                order.new_status="Open"
            else:
                order.new_status="Locked"
                
    new_status=fields.Char("Status",compute='cal_new_status')
    #Calculates The Total in The Sale_order form
    @api.depends('order_line.price_total','margin','order_line.price_subtotal')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = amount_stp =0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax

            #print("===========order_margin",amount_untaxed,order.margin)
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'amount_stp':amount_untaxed-order.margin,
            })
            print("=========+>",amount_untaxed,order.margin,amount_untaxed-order.margin)

    
    #This makes the cancel_opf_desc mandatory
    @api.multi
    def action_cancel(self):
        if self.cancel_opf_desc==False:
            raise UserError(_('OPF Cancelation Description must be specified'))
        return self.write({'state': 'cancel'})

    #function concats the lob(line_of_business) in a list as char
    def lob_list(self):
        li=[]
        oem=[]
        for order in self:
            if order.order_line:
                for i in order.order_line:
                    if i.line_of_business:
                        oem.append(i.line_of_business.line_of_business)
                    else:
                        order.lob=""
                oem_list=set(oem)
                #print("=======>",oem_list)
                oem_str=""
                for j in oem_list:
                    oem_str+=j
                order.lob=oem_str
                oem_list=[]
                oem=[]
    #amount with no decimals for display                 
    @api.depends('amount_total')
    def new_amt_total(self):
        for dt in self:
            if dt.amount_total:
                temp = dt.amount_total
                dt.amount_total_new=temp
            else:
                dt.amount_total_new=0
    #Concatinates all the vendor from dr tab
    def vendor_list(self):
        li=[]
        for order in self:
            if order.order_dr_line:
                oem=""
                for i in order.order_dr_line:
                    if i.oem1:
                        oem+=i.oem1.name + " ,"
                        order.oem=oem
                    else:
                        order.oem=""
                oem=""
    #Change the format for write date
    @api.depends('write_date')
    def new_date_write(self):
        for dt in self:
            if dt.write_date!=False:
                temp = datetime.strptime(dt.write_date,"%Y-%m-%d %H:%M:%S").date()
                dt.write_date_new=temp
                #print("======>",dt.date_order_new)
            else:
                dt.write_date_new=""
    #Change the format for Order Confirmation Date 
    @api.depends('confirmation_date')
    def new_date_confirmation(self):
        for dt in self:
            if dt.confirmation_date:
                dt.confirmation_date_new=datetime.strptime(dt.confirmation_date,"%Y-%m-%d %H:%M:%S").date()
                #print("======>",dt.confirmation_date_new)
            else:
                #print("======++>",dt.confirmation_date_new)
                dt.confirmation_date_new=""
    #Change Date Format
    @api.depends('date_order')
    def new_date_order(self):
        lang_obj=self.env['res.lang']
        lang=lang_obj.search([("name","=","English")])
        for dt in self:
            if dt.date_order!=False:
                temp = datetime.strptime(dt.date_order,"%Y-%m-%d %H:%M:%S").date()
                dt.date_order_new=temp
                #print("======>",self.date_order_new)
            else:
                dt.date_order_new=""

    
    #Validation for DR Done
    def dr_validation(self):
        for order in self:
            if order.order_dr_line:
                for i in order.order_dr_line:
                    if i.dr_done=="DR Done":
                        if i.dr_remark==False or i.dr_date==False:
                            raise UserError(_("Dr Date or Dr Remark missing"))
            else:
                raise UserError(_("Distributor must be specified"))


    # Create
    @api.model
    def create(self,values):
        res_part_obj=self.env['res.partner']
        cust_type_obj=self.env['cust.type']
        cust_type_id=cust_type_obj.search([("cust_type","=","New")])
        res_part_id=res_part_obj.search([("id","=",values['partner_id'])])
        if res_part_id.cust_type.cust_type=="Not Build":
            res_part_id.cust_type=cust_type_id.id
        line = super(SaleOrder, self).create(values)
        return line

    @api.multi
    def action_done(self):
        for order in self:
            if order.order_approve_line:
                for ids in order.order_approve_line:
                    if ids.approve_status==False:
                        raise models.ValidationError('Cannot approve.Approvals pending.')
                    else:
                        self.write({'state': 'done'}) 
            else:
                self.write({'state':'done'})

    ''' approval Flag True if all approvals are done else false'''
    def change_approve_flag(self):
        approve_list1=[]
        approve_list2=[]
        for order in self:
            if order.order_approve_line:
                for line in order.order_approve_line:
                    if line.approve_status==False:
                        approve_list1.append(line.approve_status)
                        #print("approve_list1=======>",approve_list1)
                    else:
                        approve_list2.append(line.approve_status)
                        #print('approve_list2==========>',approve_list2)
            if  len(approve_list1) == 0:
                order.approve_flag=True
            else:
                order.approve_flag=False

    '''approval stages sets approval status as done for
    user against whom approval is assigned(Validate OPF Button)'''
    @api.multi
    def approve_opf(self):
        for order in self:
            if order.order_approve_line:
                for ids in order.order_approve_line:
                    if ids.users.id==self.env.uid:
                        ids.approve_status=True
            else:
                order.approve_flag=True
        self.change_approve_flag()
        
               
    @api.multi
    def write(self,values):
        if 'revise_quote' in values:
            if values['revise_quote'] =='yes':
                self.revision_no=self.revision_no + 1
                self.revision_name="V-" + (str(self.revision_no))
                self.date_revise=datetime.now()
                values['revise_quote']='no'
        if 'opportunity_stages' in values or 'sales_stages' in values:           
            crm_obj=self.env['crm.lead']
            if self.opportunity_id.id!=False:
                crm_id=crm_obj.search([('id','=',self.opportunity_id.id)])
                crm_id.opportunity_stages=values["opportunity_stages"]
                crm_id.sales_stages=values["sales_stages"]
        if 'shrt_name' in values:
            crm_obj=self.env['crm.lead']
            if self.opportunity_id.id!=False:
                crm_id=crm_obj.search([('id','=',self.opportunity_id.id)])
                crm_id.shrt_name=values["shrt_name"]
        result = super(SaleOrder, self).write(values)
        return result

    def approval_mail(self):
        mail_details=self.env['ir.mail_server']
        server=mail_details.search([("name","=","new Server")])
        approval_list=[]
        for order in self:
            for ids in order.order_approve_line:
                approval_list.append(ids.users)
        #print('approval_list smtp host and port=============>',approval_list,server.smtp_host,server.smtp_port)
        content='Please approve OPF no.'+self.opf_name
        mail=smtplib.SMTP(server.smtp_host,server.smtp_port)
        mail.ehlo()
        mail.starttls()
        #print("SMTP User and Password==========>",server.smtp_user,server.smtp_pass)
        mail.login(server.smtp_user,server.smtp_pass)
        for i in approval_list:
            mail.sendmail(server.smtp_user,i.login,content)
        mail.quit()
    
    def order_info_validation(self):
        for order in self:
            if order.billing_location==False:
                raise UserError(_("Billing Location should not be Empty"))
            if order.client_order_ref==False:
                raise UserError(_("Customer PO and Dt. should not be Empty"))
            if (order.payment_term_id.id==False):
                raise UserError(_("Credit Terms should not be Empty"))
            if order.partner_id.vat==False:
                raise UserError(_("GSTIN should not be Empty"))
    @api.multi
    def action_confirm(self):
        self._action_confirm()
        res_part_obj=self.env['res.partner']
        cust_type_obj=self.env['cust.type']
        #Validation for DR Done
        self.dr_validation()
        #Validation for billing_location,client_order_ref,payment_term_id,vat
        self.order_info_validation()
        #Changing Type of Customer from New or Not Build to Retention
        cust_type_id=cust_type_obj.search([("cust_type","=","Retention")])
        res_part_id=res_part_obj.search([("id","=",self.partner_id.id)])
        if res_part_id.cust_type.cust_type=="Not Build" or res_part_id.cust_type.cust_type=="New":
            res_part_id.cust_type=cust_type_id.id
        #Genration of OPF sequence
        opf_seq= self.env['ir.sequence'].next_by_code('sale.order123')
        self.opf_name=opf_seq
        #Set approve flag to True if there are no Validators in Approve Tab
        self.approve_opf()
        #On create OPF send mail to approval list
        #self.approval_mail()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True
    
    

    
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res_obj=self.env['res.users']
        #print("",self.team_id.member_ids.id.user_id)
        partners_invoice = []
        partners_shipping = []
        domain = {}
        for record in self:
            if record.partner_id:
                for part in record.partner_id:
                    partners_invoice.append(part.id)
                    partners_shipping.append(part.id)
                    if record.partner_id.child_ids:
                        for partner in record.partner_id.child_ids:
                            if partner.type != 'contact':
                                partners_invoice.append(partner.id)
                            if partner.type != 'contact':
                                partners_shipping.append(partner.id)
                    if partners_invoice:
                        domain['partner_invoice_id'] =  [('id', 'in', partners_invoice)]
                    else:
                        domain['partner_invoice_id'] =  []
                    if partners_shipping:
                        domain['partner_shipping_id'] = [('id', 'in', partners_shipping)]
                        #print("print6666666666666666",partners_invoice)
                    else:
                        domain['partner_shipping_id'] =  []
            else:
                domain['partner_invoice_id'] =  [('type', '=', 'invoice')]
                #print("print7777777777777777",partners_invoice)
                domain['partner_shipping_id'] =  [('type', '=', 'delivery')]
                #print("print88888888888888",partners_invoice)
        return {'domain': domain}
               
    @api.onchange('partner_invoice_id','partner_shipping_id')
    def onchange_partner__invoice(self):
        self.partner_invoice_Add = '%s %s %s %s %s %s' %(self.partner_invoice_id.street or '' , self.partner_invoice_id.street2 or '', self.partner_invoice_id.city or '', self.partner_invoice_id.state_id.name or '', self.partner_invoice_id.zip or '', self.partner_invoice_id.country_id.name or '')
                
    @api.onchange('partner_invoice_id','partner_shipping_id')
    def onchange_partner__shipping(self):
        self.partner_shipping_Add = '%s %s %s %s %s %s' %(self.partner_shipping_id.street or '' , self.partner_shipping_id.street2 or '', self.partner_shipping_id.city or '', self.partner_shipping_id.state_id.name or '', self.partner_shipping_id.zip or '', self.partner_shipping_id.country_id.name or '')
    
    @api.multi
    def open_import_product_list(self):
        view = self.env.ref('sunfire_sales.import_product_data_view_123')
        return {
            'name': 'Import Product Data',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'magna.import',       
            'views': [(view.id, 'form')],           
            'target': 'new',
        }
    
    @api.onchange('po_to_be_placed')
    def company_addr(self):
        #print("Eureka#1",self)
        con=[]
        domain={}
        res_company_obj = self.env['res.partner']
        con_ids=res_company_obj.search([('parent_id','=',self.po_to_be_placed.id)])
        for i in con_ids:
            con.append(i.id)
        domain['po_detail_address']=[('id','in',con)]
        #print(domain)
        return {'domain':domain}
    
    @api.onchange('po_detail_address')
    def _company_full_addr(self):
        self.addr=self.po_detail_address.city
    
    @api.multi
    def action_unlock(self):
        for line in self:
            if line.order_line:
                for ids in line.order_line:
                    #print("#####action_unlock oid",myid.id,myid.po_state)
                    if ids.po_state == "NA":
                        self.write({'state': 'sale'})
                    else:
                        raise UserError(_('You can not Unlock untill PO is canceled'))
            else:
                self.write({'state','sale'})
    
    @api.onchange('partner_id')
    def _concern_person(self):
        res_partner_obj = self.env['res.partner']
        concern=[]
        domain={}
        concern_ids=res_partner_obj.search([('parent_id','=',self.partner_id.id)])
        for i in concern_ids:
            concern.append(i.id)
        domain['concern_person']=[('id','in',concern)]
        return {'domain':domain} 
            
    @api.onchange('concern_person')
    def _concern_details(self):
        self.concern_mobile=self.concern_person.mobile
        self.concern_email=self.concern_person.email
    
class delivery_term_info(models.Model):
    _name='delivery_term.info'
    _rec_name ="delivery_terms"  
    delivery_terms=fields.Char('Delivery Term')

class transport_mode_info(models.Model):
    _name = 'transport_mode.info'
    _rec_name = 'transport_modes'
    transport_modes =  fields.Char('Transport Modes')
class line_of_business_info(models.Model):
    _name = 'line_of_business.info'
    _rec_name = 'line_of_business'
    line_of_business =  fields.Char('Line of Business')
class installation_terms_info(models.Model):
    _name = 'installation_terms.info'
    _rec_name = 'installation_terms'
    installation_terms = fields.Char('Installation Terms')
class sales_stages_info(models.Model):
    _name = 'sales_stages.info'
    _rec_name = 'sales_stages'
    sales_stages = fields.Char('Sales Stages')
class opportunity_stages_info(models.Model):
    _name = 'opportunity_stages.info'
    _rec_name = 'opportunity_stages'
    opportunity_stages = fields.Char('Opportunity Stages')
class cust_type(models.Model):
    _name = 'cust.type'
    _rec_name = 'cust_type'
    cust_type = fields.Char('Customer Type')

#saleOrderLine alike tab for DR info
class dr_data_info(models.Model):
    _name="dr_data.info"
    order_dr_id = fields.Many2one('sale.order', string='Order DR Reference', ondelete='cascade', index=True, copy=False)
    oem1=fields.Many2one('res.partner',string='Vendor',required=True)
    dr_done = fields.Selection([('DR Done', 'DR Done'), ('DR Not Done', 'DR Not Done'),('DR Not Required','DR Not Required')], 'DR Done')
    dr_status = fields.Selection([('Accepted', 'Accepted'), ('Rejected', 'Rejected')], 'DR Status')
    dr_remark = fields.Char('DR Number')
    dr_date = fields.Char('DR Date')
    cross_sell=fields.Selection([('No','No'),('Yes','Yes')],'Cross Sell',default='No')
    vendor_dr_id=fields.Many2one('res.partner',string='Distributor',required=True)
    dr_no=fields.Integer(string="DR Number")
    dr_ext=fields.Boolean(string="DR Extension")
    
    @api.multi
    def unlink(self):
        ids=self.search([('order_dr_id','=',self.order_dr_id.id)])
        if len(ids)==int(1):
            raise UserError(_("Atleast One Distributor must be specified in DR Information"))
        return super(dr_data_info, self).unlink()

class deal_type_info(models.Model):
    _name="deal_type.info"
    _rec_name="deal_type"
    deal_type = fields.Char(string='Deal Type')
class upload_type_info(models.Model):
    _name="upload_type.info"
    _rec_name="upload_type"
    upload_type=fields.Char("Upload Type")
    
class upload_tab_info(models.Model):
    _name="upload_tab.info"
    order_upload_id=fields.Many2one("sale.order",string='Order Upload Reference', ondelete='cascade', index=True, copy=False)
    type=fields.Many2one("upload_type.info",string="Upload Type")
    upload_file=fields.Binary("Upload File")
    filename=fields.Char()
    verbal=fields.Text("Verbal Communication")
# class account_inv_inherit(models.Model):
#     _inherit='account.invoice'
   
#     opf_no=fields.Char('OPF No.',compute='_get_opf_name',readonly=True,store=True)
#     @api.depends('origin')
#     def _get_opf_name(self):
#         sale_order_obj=self.env["sale.order"]
#         for order in self:
#             se_id=sale_order_obj.search([('name','=',order.origin)])
#             order.opf_no = se_id.opf_name
#             print("opf_no============>",order.opf_no)
# class account_invoice_line_inherit(models.Model):
#     _inherit='account.invoice.line'             

#     opf_no=fields.Char(string="OPF No.",compute='_get_opf_name')
    
#     def _get_opf_name(self):
#         sale_order_obj=self.env["sale.order"]
#         for order in self:
#             se_id=sale_order_obj.search([('name','=',order.origin)])
#             order.opf_no = se_id.opf_name
#             print("opf_no============>",order.opf_no)
