# -*- coding: utf-8 -*-

from odoo import models, fields, api


class shopify_odoo_connector_sp(models.Model):
    _name = 'shopify_odoo_connector_sp.shopify_odoo_connector_sp'
    _description = 'shopify_odoo_connector_sp.shopify_odoo_connector_sp'

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()

    @api.depends('value')
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100
