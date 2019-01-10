from odoo import api, fields, models
from datetime import datetime

class res_partner_inhe(models.Model):
    _inherit = 'res.partner'
    
    
   # <!-- Created By:Pradip|Created Date:9-Jan-2019 |Desc. Sales Year Computed-->

    
    from_month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                          (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), 
                          (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')],'From')
    
    to_month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                          (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), 
                          (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')],'To',compute='comput_to_month',store=True)
    #from_date_day = fields.Selection([(num, str(num)) for num in range(1, (datetime.now().day)+25 )],'Expected Closing (Day)')
    
    
#     @api.onchange('from_month','to_month')
#     def from_month_val(self):
#         #print("==========================",self.from_month)
#         for m in self:
#             if m.from_month==1:
#                 m.to_month=12
#             
#             if m.from_month==2:
#                 m.to_month=1
                    
                    
    @api.depends('from_month','to_month')
    def comput_to_month(self):
        for m in self:
            
            if m.from_month==1:
                m.to_month=12
             
            if m.from_month==2:
                m.to_month=1
                
            if m.from_month==3:
                m.to_month=2
            
            if m.from_month==4:
                m.to_month=3
                
            if m.from_month==5:
                m.to_month=4
                
            if m.from_month==6:
                m.to_month=5
                
            if m.from_month==7:
                m.to_month=6
                
            if m.from_month==8:
                m.to_month=7
                
            if m.from_month==9:
                m.to_month=8
                
            if m.from_month==10:
                m.to_month=9
            
            if m.from_month==11:
                m.to_month=10
            
            if m.from_month==12:
                m.to_month=11
                