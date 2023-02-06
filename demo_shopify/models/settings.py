from odoo import fields, models


class DemoShopifySettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_webhook_status = fields.Boolean(string="Product Webhook")
    order_webhook_status = fields.Boolean(string="Order Webhook")
    customer_webhook_status = fields.Boolean(string="Customer Webhook")
