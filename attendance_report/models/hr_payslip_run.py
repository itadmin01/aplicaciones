# -*- coding: utf-8 -*-

from odoo import fields, models, api 

class hr_payslip_extends(models.Model):
    _inherit = 'hr.payslip'

    reporte_asistencia = fields.Many2one('reporte.asistencia', string="Reporte Asistencia")

    @api.model
    def get_worked_day_lines(self,contract_ids, date_from, date_to):
        res =super(hr_payslip_extends,self).get_worked_day_lines(contract_ids, date_from, date_to)
             
        #reporte_asistencia_date = self.env['reporte.asistencia'].search([('fecha_inicial','=',date_from)])
        if reporte_asistencia:
           contracts = self.env['hr.contract'].browse(contract_ids)

           lines = self.reporte_asistencia.mapped('asistencia_line_ids')
           for contract in contracts:
               employee_id = contract.employee_id.id
               emp_line_exist = lines.filtered(lambda x: x.employee_id.id==employee_id)
               if emp_line_exist:
                   emp_line_exist = emp_line_exist[0]
                   res[0].update({'number_of_days': emp_line_exist.dias_lab })
           return res

class hr_payslip_extends(models.Model):
    _inherit = 'hr.payslip.run'

    reporte_asistencia = fields.Many2one('reporte.asistencia', string="Reporte Asistencia")