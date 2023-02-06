from odoo import models, fields
from odoo.exceptions import Warning


class ImportOperations(models.TransientModel):
    _name = "create.import_options_tbl"

    instance = fields.Many2one("shopify_odoo_connector.instance_tbl", string="Instance", required=True, domain="[('state', '=', '1'),('active_status', '=', True)]")
    import_product = fields.Boolean(string="Products")
    import_customer = fields.Boolean(string="Customers")
    import_orders = fields.Boolean(string="Orders")

    # IMPORT PRODUCT
    def import_data_from_odoo_to_shopify(self):
        if self.instance.id:
            is_imported = False

            if self.import_product:
                is_imported = self.env["shopify_odoo_connector.common"].import_product_from_shopify(self.instance)
            if self.import_orders:
                is_imported = self.env['shopify_odoo_connector.common'].import_orders_from_shopify(instance=self.instance)
            if self.import_customer:
                is_imported = self.env['shopify_odoo_connector.common'].import_customers_from_shopify(instance=self.instance)

            if is_imported.get("is_import"):
                view = self.env.ref('shopify_odoo_connector.ds_success_message_wizard')
                name = 'Success'
                message = is_imported.get("message")
            else:
                view = self.env.ref('shopify_odoo_connector.ds_error_message_wizard')
                name = 'Error'
                message = is_imported.get("message")
            message_display = self.env['shopify_odoo_connector.common'].message_wizard_open(view, name, message)
            return message_display

    # EXPORT PRODUCT FROM ODOO TO SHOPIFY BY ACTION OPTION
    def export_product_by_action(self):
        if self.instance.id:
            is_exported = self.env["shopify_odoo_connector.common"].export_product_from_odoo_to_shopify_by_action(self.instance)

            if is_exported:
                # print("Product Export Successfully.")
                view = self.env.ref('shopify_odoo_connector.ds_success_message_wizard')
                name = 'Success'
                message = 'Exported Successfully.'
            else:
                view = self.env.ref('shopify_odoo_connector.ds_error_message_wizard')
                name = 'Error'
                message = 'Failed to Export products!!'
        else:
            view = self.env.ref('shopify_odoo_connector.ds_error_message_wizard')
            name = 'Error'
            message = 'Please select your instance!!'
        message_display = self.env['shopify_odoo_connector.common'].message_wizard_open(view, name, message)
        return message_display

    # EXPORT SHOPIFY PRODUCT IN ANOTHER STORE OR UPDATE IN SAME STORE
    def export_shopify_product_by_action(self):
        if self.instance.id:
            is_exported = self.env["shopify_odoo_connector.common"].export_shopify_product_by_action(self.instance)

            if is_exported.get("is_export"):
                view = self.env.ref('shopify_odoo_connector.ds_success_message_wizard')
                name = 'Success'
                message = is_exported.get("message")
            else:
                view = self.env.ref('shopify_odoo_connector.ds_error_message_wizard')
                name = 'Error'
                message = is_exported.get("message")
            message_display = self.env['shopify_odoo_connector.common'].message_wizard_open(view, name, message)
            return message_display


class ExportOperations(models.TransientModel):
    _name = "create.export_options_tbl"

    instance = fields.Many2one("shopify_odoo_connector.instance_tbl", string="Instance", required=True, domain="[('state', '=', '1'),('active_status', '=', True)]")
    from_instance = fields.Many2one("shopify_odoo_connector.instance_tbl", string="Instance", required=True, domain="[('state', '=', '1'),('active_status', '=', True)]")

    # EXPORT PRODUCT
    def export_all_products(self):
        if self.instance.id:
            is_exported = self.env["shopify_odoo_connector.common"].export_all_products_from_shopify(to_instance=self.instance,
                                                                                           from_instance=self.from_instance)

            if is_exported.get("is_export"):
                view = self.env.ref('shopify_odoo_connector.ds_success_message_wizard')
                name = 'Success'
                message = is_exported.get("message")
            else:
                view = self.env.ref('shopify_odoo_connector.ds_error_message_wizard')
                name = 'Error'
                message = is_exported.get("message")
            message_display = self.env['shopify_odoo_connector.common'].message_wizard_open(view, name, message)
            return message_display