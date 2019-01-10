from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
# create date | Create By | update date | update By
# 04/09/18      Ganesh
# Info : Following field added for tally comapny name and IP address in res_company model
class res_company_inhe(models.Model):
    _inherit = 'res.company'

    tcname = fields.Char(string='Tally Company Name')
    tipaddress = fields.Char(string='Tally IP Address')

# create date | Create By | update date | update By
# 04/09/18      Ganesh
# Info : Following field added for tally customer name in res_partner model
class Res_Partner_inhe(models.Model):
   

    _inherit = 'res.partner'

    tcustname = fields.Char(string='Tally Customer Name')
    
    
    
    
    
    
    
    
    
    
    

# create date | Create By | update date | update By
# 04/09/18      Ganesh
# Info : Following field added tally tax name in account_tax model
class account_tax_inhe(models.Model):
    _inherit = 'account.tax'
    
    ttaxname = fields.Char(string='Tally Tax Name')

