from odoo import fields,models,api,_
import datetime


class SupportTicket(models.Model):
    _name = 'support.ticket'
    _inherit='mail.thread'
    _description = 'Sunfire Support Desk'
    _rec_name='name'
    
    name = fields.Char(string='Subject',help="The Subject of the Support Ticket.")
    tag_id=fields.Many2one('support.tag',string="Tag",required=True,help="Tag of current Support Ticket. Incident/Request/Change Request/Problem")
    ticket_no=fields.Char(string="Ticket No.",store=True,help="Ticket Number of the current Support Ticket")
    channel_id=fields.Many2one('support.channel',string="Channel",help="Channel of the current Support Ticket")
    severity_id=fields.Many2one('support.severity',string="Severity",help="Severity of the current Support Ticket")
    category_id=fields.Many2one('support.category',string="Category",help="Category of the current Support Ticket")

    
    logged_date=fields.Datetime(string="Looged Time",help="Last Action Taken Time",compute='compute_logged_date')
    
    @api.multi
    def compute_logged_date(self):
        li=[]
        for actions in self:
            for action_lines in actions.action_line:
                if action_lines.write_date:
                    li.append(action_lines.write_date)
            if li!=[]:
                actions.logged_date=max(li)
            li=[]

        
    #Setting the domain of Assigned User to Technical Users
    @api.model
    def onchng_user(self):
        appr_obj=self.env['approval_types.info'].search([('approval_type','=','Technical Services')])
        li=[]
        domain={}
        for i in appr_obj.role_line:
            li.append(i.users.id)
        domain['assigned_user_id']=[('id','in',li)]
        #print("Onchange================>")
        return [('id','in',li)]
    
    assigned_user_id=fields.Many2one('res.users',string="Assigned Engineer",domain=lambda self:self.onchng_user(),track_visibility='always',help="The Technical User to whom the Ticket is to be assigned")
    partner_id=fields.Many2one('res.partner',string="Customer",help="The Customer who has raised the Ticket")
    email=fields.Char(string="Email",help="The Email of the Customer who has raised the Ticket")
    action_line=fields.One2many('support.actions','action_id',help="The Actions taken by the Assigned User on the Suppport Ticket")
    attach_line=fields.One2many('support.attach','attach_id',help="The Documents for the Support Ticket")
    description_line=fields.One2many('support.description','description_id')
    state=fields.Selection([
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'Work in Progress'),
        ('awaiting', 'Awaiting Customer'),
        ('resolved', 'Resolved'),('closed','Closed')
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='open')
    time_assign=fields.Datetime('Assign Time')
    time_resolve=fields.Datetime('Resolve Time')
    time_open=fields.Datetime('Open Time')
    time_close=fields.Datetime('Close Time')
    reassign=fields.Boolean('Reassign',default=False)
    reassign_line=fields.One2many('support.reassign','reassign_id',string='Reassigned User')
    mobile=fields.Char(string="Mobile")
    
    #Function to frwd mail on change of state
    def state_mail(self):
        email_template = self.env['ir.model.data'].get_object('sunfire_support','support_ticket_status_mail')
        email_values = email_template.generate_email([self.id])[self.id]
        email_values['model'] = "support.ticket"
        email_values['res_id'] = self.id
        #assigned_user = self.env['res.users'].browse( int(values['user_id']) )
        email_values['email_to'] = self.partner_id.email or self.email
        email_values['body_html'] = email_values['body_html'].replace("_user_name_", self.partner_id.name)
        email_values['body'] = email_values['body'].replace("_user_name_", self.partner_id.name)
        send_mail = self.env['mail.mail'].create(email_values)
        #print("here======+>")
        send_mail.send()    

    @api.multi
    def action_assigned(self):
        if self.assigned_user_id:
            values={  
                    'reassign_id':self.id,
                    'user_id':self.env.uid,
                    'reassign_user_id':self.assigned_user_id.id
                    }
            self.reassign_line.create(values)
        #self.state_mail()
        return self.write({'state': 'assigned','time_assign':datetime.datetime.now()})
    @api.multi
    def action_in_progress(self):
        #self.state_mail()
        return self.write({'state': 'in_progress'})
    @api.multi
    def action_awaiting(self):
        #self.state_mail()
        return self.write({'state': 'awaiting'})
    @api.multi
    def action_resolved(self):
        #self.state_mail()
        return self.write({'state': 'resolved','time_resolve':datetime.datetime.now()})
    @api.multi
    def action_close(self):
        #self.state_mail()
        return self.write({'state': 'closed','time_close':datetime.datetime.now()})
    #Set Email of the Customer if present else Enter on screen
    @api.onchange('partner_id')
    def set_email(self):
        if self.partner_id:
            #print(self.partner_id.child_ids.id)
            for i in self.partner_id.child_ids:
                if i.type=='cust_it_support':
                    #print(i.email,i.mobile)
                    self.email=i.email
                    self.mobile=i.mobile
    #assigns ticket number
    def set_ticket_number(self,vals):
        tag_obj=self.env['support.tag']

        tag_ids=tag_obj.search([('id','=',vals['tag_id'])])
        vals['time_open']=datetime.datetime.now()
        if tag_ids.name=="Incident":
            vals['ticket_no'] = self.env['ir.sequence'].next_by_code('website.support.ticket.incident')        
        elif tag_ids.name=="Request": 
            vals['ticket_no'] = self.env['ir.sequence'].next_by_code('website.support.ticket.request')
        elif tag_ids.name=="Change Request":
            vals['ticket_no'] = self.env['ir.sequence'].next_by_code('website.support.ticket.change_request')
        elif tag_ids.name=="Problem":
            vals['ticket_no'] = self.env['ir.sequence'].next_by_code('website.support.ticket.problem')
        else:
            vals['ticket_no'] = self.env['ir.sequence'].next_by_code('website.support.ticket')
    
    #Create Method
    @api.model
    def create(self, vals):
        self.set_ticket_number(vals)
        new_id = super(SupportTicket,self).create(vals)
        return new_id
    
    @api.multi
    def write(self,vals):
        if 'reassign' in vals and 'assigned_user_id' in vals:
            if vals['reassign']==True:
                values={  
                    'reassign_id':self.id,
                    'user_id':self.env.uid,
                    'reassign_user_id':vals['assigned_user_id']
                    }
                re_id=self.reassign_line.create(values)
                #print(re_id)
        vals['reassign']=False
        new_id = super(SupportTicket,self).write(vals)
        return new_id

#Master for Description
class SupportDescription(models.Model):
    _name='support.description'
    _rec_name='name'
    _description="Sunfire Support Description"
    name=fields.Char(string="Description",help="The Description by the User for the current Support Ticket")
    user_id=fields.Many2one('res.users',readonly=True,store=True,string="User")
    description_id=fields.Many2one('support.ticket')

    @api.model
    def create(self,vals):
        #web_obj=self.env['support.ticket'].search([('id','=',vals['description_id'])])
        vals['user_id']=self.env.uid
        new_id = super(SupportDescription, self).create(vals)
        return new_id
#Master for Attachments
class SupportAttach(models.Model):
    _name="support.attach"
    _description="Sunfire Support Attachment"
    _rec_name="name"
    name=fields.Char(string="Atachment Description",help="The Description for the Attachment attached")
    attachment=fields.Binary('Attachment',help="The Attachement to be attached for the Support Ticket")
    attach_id=fields.Many2one('support.ticket')
    filename=fields.Char('Filename')

    
#Master for Actions Taken
class SupportActions(models.Model):
    _name="support.actions"
    _description="Sunfire Support Actions"
    _rec_name="name"
    name=fields.Char(string="Actions Taken",help="The Action taken by the User for the current Support Ticket")
    assigned_user_id=fields.Many2one('res.users',readonly=True,store=True,string="Assigned User")
    action_id=fields.Many2one('support.ticket')
    wrk_loc=fields.Selection([('onsite','Onsite'),('remote','Remote')],string="Work Location")
    #action_date=fields.Date(string="Date",default=datetime.date.today(),readonly=True,store=True)
    @api.model
    def create(self,vals):
        web_obj=self.env['support.ticket'].search([('id','=',vals['action_id'])])
        vals['assigned_user_id']=web_obj.assigned_user_id.id
        new_id = super(SupportActions, self).create(vals)
        return new_id
    
#Master for Severity
class SupportCategory(models.Model):
    _name="support.category"
    _description="Sunfire Support Categories"
    _rec_name="name"
    name=fields.Char(string="Category",help="The Category To be used for Support Ticket")

#Master for Severity
class SupportSeverity(models.Model):
    _name = 'support.severity'
    _description = 'Sunfire Support severity'
    _rec_name='name'
    
    name = fields.Char(string='Severity',help="The Severity To be used for Support Ticket")

#Master for Tag
class SupportTag(models.Model):
    _name = 'support.tag'
    _description = 'Sunfire Support Tag'
    _rec_name='name'
    
    name = fields.Char(string='Tag',help="The Tag To be used for Support Ticket")

#Master for Channel
class SupportChannel(models.Model):
    _name = 'support.channel'
    _description = 'Sunfire Support Channel'
    _rec_name='name'

    name = fields.Char(string='Channel',help="The Channel To be used for Support Ticket")

class support_reassign(models.Model):
    _name='support.reassign'
    _description='Sunfire Reassignment Log'
    reassign_id=fields.Many2one('support.ticket')
    reassign_user_id=fields.Many2one('res.users',string='Reassigned User',readonly=True,store=True)
    user_id=fields.Many2one('res.users',string="Assigned UserId",readonly=True,store=True)
    #reassign_datereassign_date=fields.Date(string="Reassign Date",default=datetime.date.today(),readonly=True,store=True)
