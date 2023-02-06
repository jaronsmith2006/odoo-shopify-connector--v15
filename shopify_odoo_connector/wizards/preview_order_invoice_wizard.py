from odoo import fields, models


class OrderClass(models.TransientModel):
    _name = "create.orders"

    order_name = fields.Text(string="Name", readonly="true")
    customer_id = fields.Text(string="customer_id", readonly="true")
    line_item_id = fields.Char(string="line_item_id", readonly="true")

