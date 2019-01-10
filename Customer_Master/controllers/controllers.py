# -*- coding: utf-8 -*-
from odoo import http

# class FactoryCalendor(http.Controller):
#     @http.route('/factory_calendor/factory_calendor/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/factory_calendor/factory_calendor/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('factory_calendor.listing', {
#             'root': '/factory_calendor/factory_calendor',
#             'objects': http.request.env['factory_calendor.factory_calendor'].search([]),
#         })

#     @http.route('/factory_calendor/factory_calendor/objects/<model("factory_calendor.factory_calendor"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('factory_calendor.object', {
#             'object': obj
#         })