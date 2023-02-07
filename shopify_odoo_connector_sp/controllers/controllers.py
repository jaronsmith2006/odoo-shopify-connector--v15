# -*- coding: utf-8 -*-
from odoo import http


class DemoShopify(http.Controller):
    @http.route('/shopify_odoo_connector_sp/shopify_odoo_connector_sp', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/shopify_odoo_connector_sp/shopify_odoo_connector_sp/objects', auth='public')
    def list(self, **kw):
        return http.request.render('shopify_odoo_connector_sp.listing', {
            'root': '/shopify_odoo_connector_sp/shopify_odoo_connector_sp',
            'objects': http.request.env['shopify_odoo_connector_sp.shopify_odoo_connector_sp'].search([]),
        })

    @http.route('/shopify_odoo_connector_sp/shopify_odoo_connector_sp/objects/<model("shopify_odoo_connector_sp.shopify_odoo_connector_sp"):obj>', auth='public')
    def object(self, obj, **kw):
        return http.request.render('shopify_odoo_connector_sp.object', {
            'object': obj
        })
