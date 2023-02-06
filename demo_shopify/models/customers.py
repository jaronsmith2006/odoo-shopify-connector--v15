from odoo import fields, models, api
from datetime import datetime, date
import pytz

india = pytz.timezone('Asia/Kolkata')


class CustomersClass(models.Model):
    _name = 'ds.customers_tbl'
    _description = 'customers table'
    _rec_name = "name"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    customer_id = fields.Char(string="Customer Id")
    order_customer_id = fields.One2many("ds.order_tbl", "customer_id", string="Order Customer Id")
    name = fields.Char(string="Name")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    instance = fields.Many2one("demo_shopify.instance_tbl", string="Instance", ondelete='cascade')
    orders_count = fields.Char(string="Total Orders")
    total_spent = fields.Char(string="Total Amount Spent")
    address = fields.Char(string="Address")
    created_date = fields.Datetime(string="Created Date", default=set_date)
