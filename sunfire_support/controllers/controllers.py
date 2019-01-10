# -*- coding: utf-8 -*-
from odoo import http

# class SunfireSupport(http.Controller):
#     @http.route('/sunfire_support/sunfire_support/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sunfire_support/sunfire_support/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sunfire_support.listing', {
#             'root': '/sunfire_support/sunfire_support',
#             'objects': http.request.env['sunfire_support.sunfire_support'].search([]),
#         })

#     @http.route('/sunfire_support/sunfire_support/objects/<model("sunfire_support.sunfire_support"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sunfire_support.object', {
#             'object': obj
#         })