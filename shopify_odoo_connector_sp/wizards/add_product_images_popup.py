from odoo import fields, api, models


class ProductImageCreate(models.TransientModel):
    _name = "create.p_images_tbl"

    product_type = fields.Integer()  # 0 FOR SHOPIFY PRODUCT IMAGES, 1 FOR ODOO PRODUCT IMAGES
    product_image = fields.Binary(string="Product Image", required=True)

    def add_product_image_btn_action(self):
        self.product_type = self.env.context.get("product_type")
        vals = {
            "product_image": self.product_image
        }

        if self.product_type == 0:
            is_inserted = self.env["ds.product_images_tbl"].create(vals)
        elif self.product_type == 1:
            is_inserted = self.env["ds.odoo_product_images_tbl"].create(vals)

        if is_inserted:
            view = self.env.ref('shopify_odoo_connector_sp.ds_success_message_wizard')
            name = 'Success'
            message = 'Image added successfully.'
        else:
            view = self.env.ref('shopify_odoo_connector_sp.ds_error_message_wizard')
            name = 'Error'
            message = 'Failed to add image!!'
        message_display = self.env['shopify_odoo_connector_sp.common'].message_wizard_open(view, name, message)
        return message_display

