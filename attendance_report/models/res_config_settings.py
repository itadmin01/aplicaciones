from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    periodo = fields.Selection([('semanal', 'Semanal'),('quincenal', 'Quincenal')],
                               string='Periodo', default='quincenal')
    horas_minimo_por_dia = fields.Float(string='Horas Minimo Por Dia')
    dia_laborado = fields.Float(string='Dia Laborado')
    registros_de_asistencia = fields.Selection([('completo', 'Completo'),('parcial', 'Parcial')],
                               string='Registros de asistencia', default='completo')
    
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        res.update(
            periodo=param_obj.get_param('attendance_report.periodo'),
            registros_de_asistencia=param_obj.get_param('attendance_report.registros_de_asistencia'),
            horas_minimo_por_dia=float(param_obj.get_param('attendance_report.horas_minimo_por_dia', 0)),
            dia_laborado=float(param_obj.get_param('attendance_report.dia_laborado', 0)),
        )
        return res
 
#    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_param('attendance_report.periodo', self.periodo)
        param_obj.set_param('attendance_report.registros_de_asistencia', self.registros_de_asistencia)
        param_obj.set_param('attendance_report.horas_minimo_por_dia', self.horas_minimo_por_dia)
        param_obj.set_param('attendance_report.dia_laborado', self.dia_laborado)
        return res
    
    