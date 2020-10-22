# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, tools
import babel
from datetime import date, datetime, time

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    proyeccion = fields.Boolean(string='Proyeccion')
    
    def genera_prenomina(self):
        periodicidad = self.periodicidad_pago
        contracts = self.env['hr.contract'].search([('state','=','open'),('periodicidad_pago','=',periodicidad)])
        payslips = self.env['hr.payslip']
        ttyme = datetime.combine(fields.Date.from_string(self.date_start), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        if contracts:
            for contract in contracts:
                slip_data = self.env['hr.payslip'].onchange_employee_id(self.date_start, self.date_end, contract.employee_id.id, contract_id=False)
                vals = {
                    'employee_id': contract.employee_id.id,
                    'name': _('Nómina salarial de  %s para %s') % (contract.employee_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
                    'struct_id': self.estructura and self.estructura.id or contract.struct_id.id,
                    'contract_id': contract.id,
                    'payslip_run_id': self.id,
                    'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                    'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                    'date_from': self.date_start,
                    'date_to': self.date_end,
                    'company_id': contract.company_id and contract.company_id.id,
                    'tipo_nomina' : self.tipo_nomina,
                    'fecha_pago' : self.fecha_pago,
                    'no_nomina': self.no_nomina,
                    'mes': '{:02d}'.format(self.date_end.month),
                }
                payslips += self.env['hr.payslip'].create(vals)
            return {'type': 'ir.actions.act_window_close'}
                
            
        
