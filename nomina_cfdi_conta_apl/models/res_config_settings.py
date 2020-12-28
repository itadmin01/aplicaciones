# -*- coding: utf-8 -*-

from odoo import api, fields, models
from ast import literal_eval

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    tipo_de_poliza = fields.Selection([('Por empleado', 'Por empleado'), ('Por nómina', 'Por procesamiento')], string='Tipo de poliza')
    department_ids = fields.Many2many('hr.department',string="Departamentos")
    
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        departments = param_obj.get_param('nomina_cfdi_conta_apl.department_ids')
        res.update(
            tipo_de_poliza = param_obj.get_param('nomina_cfdi_conta_apl.tipo_de_poliza'),
            department_ids = [(6, 0, literal_eval(departments))] if departments else False,
        )
        return res
    
#     @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_param('nomina_cfdi_conta_apl.tipo_de_poliza', self.tipo_de_poliza)
        param_obj.set_param('nomina_cfdi_conta_apl.department_ids', self.department_ids.ids)
        return res
    
    