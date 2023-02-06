from odoo import fields, api, models
from datetime import datetime, date
import pytz

india = pytz.timezone('Asia/Kolkata')


class VariantInventoryModel(models.Model):
    _name = "ds.variant_inventory_tbl"
    _description = "ds.variant_inventory_tbl"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    product_id = fields.Many2one("ds.products_tbl", string="Product Name", ondelete='cascade')
    instance = fields.Many2one("shopify_odoo_connector.instance_tbl", string="Instance")
    inventory_item_id = fields.Char(string="Inventory Item Id")
    variant_id = fields.Many2one("ds.products_variants_tbl", string="Variant", ondelete='cascade')
    variant_location_id = fields.Many2one("ds.locations_tbl", string="Variant Location", ondelete='cascade')
    location_id = fields.Char(string="Location Id")
    location_name = fields.Char(string="Location")
    available = fields.Integer(string="Quantity")
    created_date = fields.Datetime(string="Created Date", default=set_date)