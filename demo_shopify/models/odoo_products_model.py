from odoo import fields, models, api
from datetime import datetime, date
import base64
import pytz

india = pytz.timezone('Asia/Kolkata')

class OdooProductModel(models.Model):
    _name = "ds.odoo_products_tbl"
    _description = "ds.odoo_products_tbl"
    _rec_name = "product_title"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    product_title = fields.Char(string="Product Name")
    product_status = fields.Selection([
        ('active', 'Active'),
        ('draft', 'Draft'),
    ], default="active", string="Product Status")
    product_price = fields.Float(string="Sale Price")
    product_image = fields.Binary(string="Product Image")
    description = fields.Text(string="Description")
    vendor = fields.Char(string="Vendor")
    tags = fields.Text(string="Tags")
    p_images = fields.One2many("ds.odoo_product_images_tbl", "product_id", string="Odoo Product All Images")
    exported_in = fields.Many2many("demo_shopify.instance_tbl", string="Exported Instances")
    product_options = fields.One2many("ds.odoo_product_options", "odoo_op_product_id", string="Product Options")
    product_variants = fields.One2many("ds.odoo_products_variants_tbl", "product_id", string="Product Variant Ids")
    created_date = fields.Datetime(string="Created Date", default=set_date)

    @api.onchange('product_options')
    def create_variants(self):
        if self.product_options:
            variants = self.env['demo_shopify.common'].create_variant_onchange('ds.odoo_products_variants_tbl', self.product_options)
            self.write({'product_variants': variants})
        else:
            print("No Options")
        return

# @api.depends('product_options')
    # def create_variants(self):
    #     if self.product_options:
    #         product_variants_ids_arr = []
    #         options_values1_arr = []
    #         options_values2_arr = []
    #         value_arr = []
    #         for op_id in self.product_options:
    #             search_option_value = self.env['ds.odoo_product_options'].search([
    #                 ('id', '=', op_id.id)
    #             ])
    #
    #             # option_value_ids_arr = []
    #             value_arr = []
    #             if search_option_value:
    #                 for option_value_id in search_option_value:
    #                     op_val_arr = []
    #                     for val_id in option_value_id.op_val_id:
    #                         op_val_arr.append(val_id.id)
    #
    #                     print("op_val_arr: ", op_val_arr)
    #
    #                     for op_val_id in op_val_arr:
    #                         get_option_value_title = self.env['ds.product_options_values'].search([
    #                             ('id', '=', op_val_id)
    #                         ])
    #
    #                         if get_option_value_title:
    #                             value_arr.append(get_option_value_title.option_value)
    #
    #             if not options_values2_arr and options_values1_arr:
    #                 options_values2_arr = value_arr
    #
    #             if not options_values1_arr:
    #                 options_values1_arr = value_arr
    #
    #         final_values_arr = []
    #         if value_arr and options_values1_arr and not options_values2_arr:
    #             for value1 in options_values1_arr:
    #                 for value2 in value_arr:
    #                     final_values_arr.append("{} / {}".format(value1, value2))
    #         elif value_arr and options_values1_arr and options_values2_arr:
    #             for value1 in options_values1_arr:
    #                 for value2 in options_values2_arr:
    #                     for value3 in value_arr:
    #                         final_values_arr.append("{} / {} / {}".format(value1, value2, value3))
    #
    #         if final_values_arr:
    #             for variant_title in final_values_arr:
    #                 variant_data = {
    #                     'title': variant_title,
    #                 }
    #
    #                 insert_variant = self.env['ds.odoo_products_variants_tbl'].create(variant_data)
    #
    #                 if insert_variant:
    #                     product_variants_ids_arr.append(insert_variant.id)
    #         self.product_variants = product_variants_ids_arr
    #     else:
    #         self.product_variants = ()
    #     return


class OdooProductImages(models.Model):
    _name = 'ds.odoo_product_images_tbl'
    _description = "ds.odoo_product_images_tbl"
    _rec_name = "product_id"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    product_id = fields.Many2one("ds.odoo_products_tbl", string="Product", ondelete='cascade')
    product_image = fields.Binary(string="Product Image")
    created_date = fields.Datetime(string="Created Date", default=set_date)

    def delete_product_image(self):
        is_delete = self.search([("id", "=", self.id)]).unlink()

        if is_delete:
            view = self.env.ref('demo_shopify.ds_success_message_wizard')
            name = 'Success'
            message = 'Deleted Successfully.'
        else:
            view = self.env.ref('demo_shopify.ds_error_message_wizard')
            name = 'Error'
            message = 'Failed to Delete!!'
        message_display = self.env['demo_shopify.common'].message_wizard_open(view, name, message)
        return message_display

class OdooProductOptions(models.Model):
    _name = "ds.odoo_product_options"
    _description = "ds.odoo_product_options"
    _rec_name = "option_name"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    odoo_op_product_id = fields.Many2one("ds.odoo_products_tbl", string="Product Name", ondelete='cascade')
    option_name = fields.Char("Option Name")
    option_position = fields.Integer("Option Position")
    op_val_id = fields.Many2many("ds.product_options_values", string="Option Value")
    created_date = fields.Datetime(string="Created Date", default=set_date)


class OdooProductVariantModel(models.Model):
    _name = "ds.odoo_products_variants_tbl"
    _description = "ds.odoo_products_variants_tbl"
    _rec_name = "title"

    @api.model
    def set_date(self):
        return (datetime.now(india)).strftime("%Y-%m-%d %H:%M:%S")

    product_id = fields.Many2one("ds.odoo_products_tbl", string="Product Name", ondelete='cascade')
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
    inventory_quantity = fields.Char(string="Inventory Quantity")
    old_inventory_quantity = fields.Char(string="Old Inventory Quantity")
    created_date = fields.Datetime(string="Created Date", default=set_date)

