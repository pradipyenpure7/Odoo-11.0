from odoo import api, fields, models


class ModuleName(models.Model):
    _name = 'module.name'
    _description = 'New Description'

    name = fields.Char(string='Name')
