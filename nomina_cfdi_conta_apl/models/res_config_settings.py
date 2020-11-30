# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    tipo_de_poliza = fields.Selection([('Por empleado', 'Por empleado'), ('Por nómina', 'Por procesamiento')], string='Tipo de poliza')
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        res.update(
            tipo_de_poliza = param_obj.get_param('nomina_cfdi_conta_apl.tipo_de_poliza'),
        )
        return res
    
#     @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_param('nomina_cfdi_conta_apl.tipo_de_poliza', self.tipo_de_poliza)
        return res