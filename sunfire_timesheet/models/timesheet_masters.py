from odoo import api,models,fields
#Master For Category and SubCategory
class category_info(models.Model):
    _name="category.info"
    _rec_name="category"
    category=fields.Char("Category")
    catg_line=fields.One2many('sub_category.info','category_id')
    role=fields.Many2one('approval_types.info',string="Role")

class sub_category_info(models.Model):
    _name="sub_category.info"
    _rec_name="sub_category"
    sub_category=fields.Char("Sub Category")
    category_id=fields.Many2one('category.info',string='Category')
    role=fields.Many2one('approval_types.info',string="Role")

    @api.onchange('role')
    def onchng_role(self):
        if self.role:
            categ_obj=self.env['category.info']
            categ_id=categ_obj.search([('role','=',self.role.id)])
            li=[]
            domain={}
            for i in categ_id:
                li.append(i.id)
            domain['category_id']=[('id','in',li)]
            return {'domain':domain}
