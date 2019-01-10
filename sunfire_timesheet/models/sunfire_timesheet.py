from odoo import api, fields, models,_
import datetime
from odoo.exceptions import UserError
class sunfire_timesheet(models.Model):
    _name = 'sunfire.timesheet'
    _rec_name='timesheet_date'
    _description="Timesheet Header"
    _sql_constraints = [ ('unique_date', 'unique(timesheet_date,create_uid)', 'Timesheet of the date entered already exists')	]
    name = fields.Char(string='Name')
    timesheet_date=fields.Date("Timesheet Date",required=True,default=datetime.date.today())
    timesheet_line=fields.One2many("sunfire.timesheet.line","timesheet_id",string="XYZ")
    total_time = fields.Float(string='Total time(minuntes)',compute='compute_time')
    total_time_hrs=fields.Char(string="Total Time (hh:mm)",compute='compute_time',readonly=True)
    
    #Computed field for calculating total time
    @api.depends('timesheet_line.timespent')
    def compute_time(self):
        for line in self:
            temp=datetime.timedelta(hours=0.0)
            if line.timesheet_line:
                for time in line.timesheet_line:
                    if time.timespent:
                        temp+=datetime.timedelta(hours=time.timespent)
                line.total_time_hrs=str(temp).rsplit(':',1)[0]

    #Validation for timesheet_date(should not be greater than todays date)
    @api.constrains('timesheet_date')
    def date_validation(self):
        if self.timesheet_date:
            timesheet_date=datetime.datetime.strptime(self.timesheet_date,"%Y-%m-%d").date()
            if timesheet_date > datetime.date.today():
                raise UserError(_("Timesheet Date should not be greater than Today's Date"))

class sunfire_timesheet_line(models.Model):
    _name="sunfire.timesheet.line"
    _description="Timesheet Detail"

    @api.model
    def set_role(self):
        app_obj=self.env['approval_type_line.info']
        app_id=app_obj.search([('users','=',self.env.uid)])
        if app_id:
            li=[]
            domain={}
            for r in app_id:
                li.append(r.approval_id.id)
            domain['role_type']=[('id','in',li)]
            return [('id','in',li)]
    role_type=fields.Many2one('approval_types.info',string="Role",domain=lambda self:self.set_role(),required=True)
   
    @api.model
    def category_domain(self):
        app_obj=self.env['approval_type_line.info']
        app_id=app_obj.search([('users','=',self.env.uid)])
        li=[]
        domain={}
        for order in app_id:
           # print("In domain Category",order)
            sub_cat_obj=order.env['category.info']
            sub_cat_ids=sub_cat_obj.search([('role','=',order.approval_id.id)])
            if sub_cat_ids:
                for j in sub_cat_ids:
                    #print("@@@@@@@@@JJJJJJ",j)
                    li.append(j.id)
                domain['category']=[('id','in',li)]
                return [('id','in',li)] 
    category=fields.Many2one('category.info',string="Category",domain=lambda self: self.category_domain())
    
    @api.model
    def sub_categ_domain(self):
        app_obj=self.env['approval_type_line.info']
        app_id=app_obj.search([('users','=',self.env.uid)])
        li=[]
        domain={}
        for order in app_id:
            sub_cat_obj=order.env['sub_category.info']
            sub_cat_ids=sub_cat_obj.search([('role','=',order.approval_id.id)])
            if sub_cat_ids:
                for j in sub_cat_ids:
                    #print("@@@@@@@@@JJJJJJ",j)
                    li.append(j.id)
                domain['sub_category']=[('id','in',li)]
                return [('id','in',li)]
    sub_category=fields.Many2one('sub_category.info',string='Sub-category',domain=lambda self: self.sub_categ_domain())

    customer=fields.Many2one('res.partner',string='Customer')
    timespent=fields.Float("Time Spent")
    timesheet_id=fields.Many2one('sunfire.timesheet',string="XYZ")
    remark=fields.Char(string="Remarks")
    rep_date=fields.Date(related="timesheet_id.timesheet_date")
    outcome=fields.Char(string="Outcome")
    poa=fields.Char(string="POA")
   
    lead_id=fields.Many2one('crm.lead')
   
    #Checks whether customer is present while createing crm_lead
    def _set_cust(self,vals):
        if 'customer' in vals:
            if vals['customer']:
                cust=vals['customer']
                return cust
            else:
                raise UserError(_("For Category \"Opportunity Created\" Customer must be specified"))
        elif self.customer:
            cust=self.customer
            return cust.id
        else:
            raise UserError(_("For Category \"Opportunity Created\" Customer must be specified"))
        
    #Checks whether POA is present while createing crm_lead
    def _set_poa(self,vals):
        if 'poa' in vals:
            if vals["poa"]:
                poa=vals['poa']
            else:
                raise UserError(_("For Category 'Opportunity Created' POA must be specified"))
        elif self.poa:
            poa=self.poa
        else:
            raise UserError(_("For Category 'Opportunity Created' POA must be specified"))
        return poa
    #Checks whether Outcome is present while createing crm_lead
    def _set_outcome(self,vals):
        if 'outcome' in vals:
            if vals["outcome"]:
                outcome=vals['outcome']
            else: raise UserError(_("For Category 'Opportunity Created' Outcome must be specified"))
        elif self.outcome:
            outcome=self.outcome
        else:
            raise UserError(_("For Category 'Opportunity Created' Outcome must be specified"))
        return outcome
    #if category is Opportunity Created then create crm_lead
    def timesheet_action_lead_new(self,vals):
        if 'category' in vals:
            cat_obj=self.env['category.info']
            temp='Opportunity Created'
            if 'role_type' in vals:
                cat_id=cat_obj.search([('category','=',temp),('role','=',vals['role_type'])])
            else:
                cat_id=cat_obj.search([('category','=',temp),('role','=',self.role_type.id)])
            if vals['category'] == cat_id.id:
                cust=self._set_cust(vals)
                poa=self._set_poa(vals)
                outcome=self._set_outcome(vals)
                desc='POA: '+ poa +'  Outcome: '+ outcome
                res_part_obj=self.env['res.partner']
                crm_lead_obj=self.env['crm.lead']
                res_part_id=res_part_obj.search([('id','=',cust)])
                lead_vals= {
                            'name':'DAR Extract' +' - '+res_part_id.name,
                            'partner_id':res_part_id.id,
                            'crm_pricelist_id':1,
                            'description':desc             
                    }
                crm_lead_obj_id = crm_lead_obj.create(lead_vals)
                vals['lead_id']=crm_lead_obj_id.id
                #print("Lead Create by====>",self.env.uid)

    #Create method overridden to create crm_lead while saving
    @api.model
    def create(self,vals):
        self.timesheet_action_lead_new(vals)
        line = super(sunfire_timesheet_line, self).create(vals)            
        return line

    #Write method overridden to create crm_lead while saving
    @api.multi
    def write(self,vals):
        if self.lead_id:
            crm_lead_obj=self.env['crm.lead']
            crm_id=crm_lead_obj.search([('id','=',self.lead_id.id)])
            if "customer" in vals:
                crm_id.partner_id=vals['customer']
                crm_id.name='DAR Extract' +' - '+ crm_id.partner_id.name
            elif "poa" in vals or "outcome" in vals:
                crm_id.description='POA: '+ (vals['poa'] or self.poa) +'  Outcome: '+(vals['outcome'] or self.outcome)
        else:
            if 'category' in vals:
                self.timesheet_action_lead_new(vals)
        line = super(sunfire_timesheet_line, self).write(vals)
        return line

    
    #Calculates Domain for Category in Timesheet Details
    def set_categ(self):
        for order in self:
            if order.role_type:
                li=[]
                domain={}
                sub_cat_obj=order.env['category.info']
                sub_cat_ids=sub_cat_obj.search([('role','=',order.role_type.approval_type)])
                for j in sub_cat_ids:
                    li.append(j.id)
                domain['category']=[('id','in',li)]
                return domain    

    #ONchange Category Set SubCategory domain plus validation for Category
    @api.onchange('category')
    def set_sub_categ(self):
        if self.category:
            if self.role_type:
                catg_obj=self.env['sub_category.info']
                subcatg_list=[]
                domain={}
                for order in self:
                    if order.category:
                        for ids in order.category:
                            catg_ids=catg_obj.search([('category_id','=',ids.id),('role','=',order.role_type.approval_type)])
                            if catg_ids:
                                #print("No Error",catg_ids)
                                for order in catg_ids:
                                    subcatg_list.append(order.id)
                                domain['sub_category']=[('id','in',subcatg_list)]
                            else:
                                #print("new error")
                                raise UserError(_("Category And Role Doesnt match"))
                return {'domain':domain}
            else:
                raise UserError(_("Should select Role first"))

    #Onchange set role type
    @api.onchange('role_type')
    def onchgcatg(self):
        if self.role_type:
            domain=self.set_categ()
            return {'domain':domain}

    #onchange validation for subcategory
    @api.onchange('sub_category')
    def onchng_subCateg(self):
        if self.sub_category:
            if not self.category:
                raise UserError(_("Should select Category first"))
