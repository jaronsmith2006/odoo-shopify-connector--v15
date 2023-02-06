from odoo import fields, api, models
from datetime import datetime, date
import pytz

india = pytz.timezone('Asia/Kolkata')


class SalesProductsClass(models.Model):
    _inherit = 'product.template'

    instance = fields.Many2one("demo_shopify.instance_tbl", String="Instance", ondelete="cascade")
    product_id = fields.Char(string="Product ID")


class ProductModel(models.Model):
    _name = 'ds.products_tbl'
    _description = "ds.products_tbl"
    _rec_name = "instance"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    def name_get(self):
        res = []
        for field in self:
            if self.env.context.get('active_model'):
                instance = field.instance.store_name
                res.append((field.id, '%s - %s' % (instance, field.product_title)))
            else:
                res.append((field.id, field.product_title))
        return res

    product_id = fields.Char(string="Product ID")
    product_title = fields.Char(string="Product Name")
    product_status = fields.Selection([
        ('active', 'Active'),
        ('draft', 'Draft'),
    ], default="active", string="Product Status")
    product_price = fields.Float(string="Sale Price", default=1)
    product_image = fields.Binary(string="Product Image")
    p_images = fields.One2many("ds.product_images_tbl", "product_id", string="Product All Images")
    description = fields.Text(string="Description")
    vendor = fields.Char(string="Vendor")
    tags = fields.Text(string="Tags")
    instance = fields.Many2one("demo_shopify.instance_tbl", string="Instance", ondelete="cascade")
    product_options = fields.One2many("ds.product_options", "op_product_id", string="Product Options")
    product_variants = fields.One2many("ds.products_variants_tbl", "product_id", string="Product Id")
    exported_instance = fields.Many2many("demo_shopify.instance_tbl", string="Exported Instance", default="")
    exported_instances_and_ids = fields.Text(string="Exported Instances And Their Ids", default="")
    odoo_product_id = fields.Integer(string="Odoo Product Id", default='0')
    created_date = fields.Datetime(string="Created Date", default=set_date)
    updated_date = fields.Datetime(string="Updated Date", default=None)

    def write(self, vals):
        vals['updated_date'] = (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")
        return super(ProductModel, self).write(vals)  # InstanceClass is class name

    @api.onchange('product_options')
    def create_variants(self):
        if self.product_options:
            variants = self.env['demo_shopify.common'].create_variant_onchange('ds.products_variants_tbl', self.product_options, self.instance.id, self._origin.id)
            # self.product_variants = variants
            self.write({'product_variants': variants})
            # self.env.ref('ds.products_tbl').write({'product_variants': variants})
        else:
            print("No Options")
        return

    # EDIT AND EXPORT PRODUCT IN STORE
    def edit_and_export_to_shopify(self):
        # is_exported = self.env["demo_shopify.common"].edit_and_export_product_by_button(self, self.instance)
        is_exported = self.env["demo_shopify.common"].edit_and_export_product_by_button(self)

        if is_exported:
            view = self.env.ref('demo_shopify.ds_success_message_wizard')
            name = 'Success'
            message = 'Edit & Exported Successfully.'
        else:
            view = self.env.ref('demo_shopify.ds_error_message_wizard')
            name = 'Error'
            message = 'Failed to Export!!'
        message_display = self.env['demo_shopify.common'].message_wizard_open(view, name, message)
        return message_display

class ProductImages(models.Model):
    _name = 'ds.product_images_tbl'
    _description = "ds.product_images_tbl"
    _rec_name = "product_id"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    product_id = fields.Many2one("ds.products_tbl", string="Product", ondelete='cascade')
    product_image = fields.Binary(string="Product Image")
    created_date = fields.Datetime(string="Created Date", default=set_date)

    def delete_product_image(self):
        is_delete = self.search([("id", "=", self.id)]).unlink()
        if not is_delete:
            self.env["demo_shopify.common"].write_error_log("Product Image delete in products_model.py file.", "Product Image not deleted properly.")


class ProductOptions(models.Model):
    _name = "ds.product_options"
    _description = "demo_shopify.product_options"
    _rec_name = "option_name"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    product_id = fields.Char(string="Product Id")
    op_product_id = fields.Many2one("ds.products_tbl", string="Product Name", ondelete='cascade')
    instance_id = fields.Many2one("demo_shopify.instance_tbl", string="Instance")
    option_id = fields.Char("Option Id")
    option_name = fields.Char("Option Name")
    option_position = fields.Integer("Option Position")
    op_val_id = fields.Many2many("ds.product_options_values", string="Option Value")
    created_date = fields.Datetime(string="Created Date", default=set_date)


class ProductOptionsValues(models.Model):
    _name = "ds.product_options_values"
    _description = "demo_shopify.product_options_values"
    _rec_name = "option_value"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    option_value = fields.Char("Options Values")
    created_date = fields.Datetime(string="Created Date", default=set_date)


class ProductVariantModel(models.Model):
    _name = "ds.products_variants_tbl"
    _description = "ds.products_variants_tbl"
    _rec_name = "title"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    instance_id = fields.Many2one("demo_shopify.instance_tbl", string="Instance")
    product_id = fields.Many2one("ds.products_tbl", string="Product Name", ondelete='cascade')
    variant_id = fields.Char(string="Variant Id")
    title = fields.Text(string="Title")
    variant_image = fields.Binary(string="Variant Image")
    price = fields.Float(string="Price")
    compare_at_price = fields.Float(string="Compare At Price")
    sku = fields.Text(string="SKU")
    barcode = fields.Text(string="Barcode")
    grams = fields.Char(string="Grams")
    weight = fields.Char(string="Weight")
    weight_unit = fields.Char(string="Weight Unit")
    inventory_item_id = fields.Char(string="Inventory Item Id")
    all_location_names = fields.Many2many("ds.locations_tbl", string="Location Name")
    inventory_data = fields.One2many("ds.variant_inventory_tbl", "variant_id", string="Location Data")
    inventory_quantity = fields.Integer(string="Inventory Quantity", readonly=True)
    old_inventory_quantity = fields.Integer(string="Old Inventory Quantity")
    created_date = fields.Datetime(string="Created Date", default=set_date)

