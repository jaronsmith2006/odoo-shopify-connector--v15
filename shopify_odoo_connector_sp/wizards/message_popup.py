from odoo import api, fields, models, _


class MessageWizard(models.TransientModel):
    _name = "ds.message_wizard"
    _description = "Message Wizard"

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    name = fields.Text(string="Message", readonly=True, default=get_default)

