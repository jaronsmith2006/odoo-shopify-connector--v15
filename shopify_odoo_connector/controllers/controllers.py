# -*- coding: utf-8 -*-
from odoo import http


class DemoShopify(http.Controller):
    @http.route('/shopify_odoo_connector/shopify_odoo_connector', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/shopify_odoo_connector/shopify_odoo_connector/objects', auth='public')
    def list(self, **kw):
        return http.request.render('shopify_odoo_connector.listing', {
            'root': '/shopify_odoo_connector/shopify_odoo_connector',
            'objects': http.request.env['shopify_odoo_connector.shopify_odoo_connector'].search([]),
        })

    @http.route('/shopify_odoo_connector/shopify_odoo_connector/objects/<model("shopify_odoo_connector.shopify_odoo_connector"):obj>', auth='public')
    def object(self, obj, **kw):
        return http.request.render('shopify_odoo_connector.object', {
            'object': obj
        })
