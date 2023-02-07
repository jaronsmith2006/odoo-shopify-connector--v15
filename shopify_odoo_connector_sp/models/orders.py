from odoo import fields, api, models
from datetime import datetime, date
import pytz

india = pytz.timezone('Asia/Kolkata')


class OrderClass(models.Model):
    _name = "ds.order_tbl"
    _description = "Order Table"
    _rec_name = "order_name"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

        # con_date = (datetime.now(india)).strftime("%d-%m-%Y %H:%M:%S")
        # print("condate: ", con_date)
        # return con_date
        # return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    @api.model
    def date_convert(self):
        date_time_obj = datetime.strptime(self, '%Y-%m-%d %H:%M:%S')
        return date_time_obj

    order_id = fields.Char(string="Order Id")
    order_name = fields.Char(string="Name")
    shipping_address = fields.Char(string="Shipping Address")
    instance_id = fields.Many2one("shopify_odoo_connector_sp.instance_tbl", string="Instance", ondelete='cascade')
    customer_id = fields.Many2one("ds.customers_tbl", string="Customer", ondelete='cascade')
    line_item_id = fields.One2many("ds.order_line_items_tbl", "inserted_order_id", string="Product Options", default=None)
    is_one2many_field_empty = fields.Boolean("Line item available", compute="_compute_is_one2many_field_empty", default=False)
    order_date = fields.Char(store=True)
    o_date = fields.Char(string="Order Date", compute='date_convert')
    fulfillment_status = fields.Char(string="Fulfillment Status")
    payment_status = fields.Char(string="Payment Status")
    subtotal_price = fields.Char(string="Subtotal Price")
    total_discounts = fields.Char(string="Total Discount")
    total_tax = fields.Char(string="Total Tax")
    total_price = fields.Char(string="Total Price")
    created_date = fields.Datetime(string="Created Date", default=set_date)

    @api.depends('order_date')
    def date_convert(self):
        for rec in self:
            rec.o_date = ''
            if rec.order_date:
                con_date = datetime.strptime(rec.order_date, "%Y-%m-%dT%H:%M:%S%z")
                o_date = con_date.date().strftime("%Y-%m-%d")
                o_time = con_date.time().strftime("%H:%M:%S")
                rec.o_date = "{} {}".format(o_date, o_time)

    def action_order_sync(self):
        for order in self:
            is_imported = self.env['shopify_odoo_connector_sp.common'].sync_order_from_shopify(instance=self.instance_id, order=order.order_id)
            if is_imported.get("is_import"):
                view = self.env.ref('shopify_odoo_connector_sp.ds_success_message_wizard')
                name = 'Success'
                message = is_imported.get("message")
            else:
                view = self.env.ref('shopify_odoo_connector_sp.ds_error_message_wizard')
                name = 'Error'
                message = is_imported.get("message")
            message_display = self.env['shopify_odoo_connector_sp.common'].message_wizard_open(view, name, message)
            return message_display

    def action_order_print_invoice(self):
        return self.env.ref('shopify_odoo_connector_sp.record_id').report_action(self)

    @api.depends('line_item_id')
    def _compute_is_one2many_field_empty(self):
        i = 1
        for record in self:
            i = i+1
            record.is_one2many_field_empty = not bool(record.line_item_id.filtered(lambda r: r.id))

class OrderLineItems(models.Model):
    _name = 'ds.order_line_items_tbl'
    _description = 'Shopify Orders Line Items'
    _rec_name = 'product_id'

    line_item_id = fields.Char(string="ID")
    sku = fields.Text(string="SKU")
    product_id = fields.Many2one("ds.products_tbl", string="Product", ondelete='cascade')
    order_id = fields.Char(string="Order ID")
    inserted_order_id = fields.Many2one("ds.order_tbl", string="Order Name", ondelete='cascade')
    fulfill_qty = fields.Char(string="Fulfill Quantity")
    price = fields.Char(string="Price")
    quantity = fields.Char(string="Quantity")
    instance_id = fields.Many2one("shopify_odoo_connector_sp.instance_tbl", string="Instance")