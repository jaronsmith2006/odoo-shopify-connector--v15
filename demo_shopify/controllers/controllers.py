# -*- coding: utf-8 -*-
from odoo import http


class DemoShopify(http.Controller):
    @http.route('/demo_shopify/demo_shopify', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/demo_shopify/demo_shopify/objects', auth='public')
    def list(self, **kw):
        return http.request.render('demo_shopify.listing', {
            'root': '/demo_shopify/demo_shopify',
            'objects': http.request.env['demo_shopify.demo_shopify'].search([]),
        })

    @http.route('/demo_shopify/demo_shopify/objects/<model("demo_shopify.demo_shopify"):obj>', auth='public')
    def object(self, obj, **kw):
        return http.request.render('demo_shopify.object', {
            'object': obj
        })
