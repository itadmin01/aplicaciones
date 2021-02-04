# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, tools
import babel
from datetime import date, datetime, time
import logging
_logger = logging.getLogger(__name__)

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    proyeccion = fields.Boolean(string='Proyeccion')
    periodo_anterior = fields.Many2one('hr.payslip.run', string='Periodo anterior')
    
    def genera_prenomina(self):
        periodicidad = self.periodicidad_pago
        contracts = self.env['hr.contract'].search([('state','=','open'),('periodicidad_pago','=',periodicidad)])
        payslips = self.env['hr.payslip']
        ttyme = datetime.combine(fields.Date.from_string(self.date_start), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        batch_last_id = self.periodo_anterior
        other_inputs = []
        for other in self.tabla_otras_entradas:
            if other.descripcion and other.codigo: 
                other_inputs.append((0,0,{'name':other.descripcion, 'code': other.codigo, 'amount':other.monto}))
        if contracts:
            for contract in contracts:
                if contract.employee_id:
                   slip_data = self.env['hr.payslip'].onchange_employee_id(self.date_start, self.date_end, contract.employee_id.id, contract_id=False)
                   new_worked_days = []
                   new_days = 0
                   work_days_now = slip_data['value'].get('worked_days_line_ids')
                   for days_now in work_days_now:
                      if days_now['code'] == 'INC_EG' or days_now['code'] == 'INC_RT' or days_now['code'] == 'INC_MAT':
                          new_worked_days.append({
                              'name': days_now['name'],
                              'sequence': days_now['sequence'],
                              'code': days_now['code'],
                              'number_of_days': days_now['number_of_days'],
                              'number_of_hours': days_now['number_of_hours'],
                              'contract_id': days_now['contract_id'],
                          })
                          new_days += days_now['number_of_days']
                      if self.reporte_asistencia:
                          asistencia_lines = self.reporte_asistencia.mapped('asistencia_line_ids')
                          employee_id = contract.employee_id.id
                          emp_line_exist = asistencia_lines.filtered(lambda x: x.employee_id.id==employee_id)
                          dias_lab = 0
                          if emp_line_exist:
                              emp_line_exist = emp_line_exist[0]
                              dias_lab =  emp_line_exist.dias_lab
                          new_worked_days.append({
                                'name': "Días de trabajo",
                                'sequence': 1,
                                'code': 'WORK100',
                                'number_of_days': dias_lab,
                                'number_of_hours': dias_lab * 8,
                                'contract_id': slip_data['value'].get('contract_id'),
                          })
                      else:
                          new_worked_days.append({
                                'name': "Días de trabajo",
                                'sequence': 1,
                                'code': 'WORK100',
                                'number_of_days': self.dias_pagar - new_days,
                                'number_of_hours': (self.dias_pagar - new_days) * 8,
                                'contract_id': slip_data['value'].get('contract_id'),
                          })
                   if batch_last_id:
                      slip_data2 = self.env['hr.payslip'].onchange_employee_id(batch_last_id.date_start, batch_last_id.date_end, contract.employee_id.id, contract_id=False)
                      work_days_previous = slip_data2['value'].get('worked_days_line_ids')
                      for days_now2 in work_days_previous:
                         if days_now2['code'] != 'INC_EG' and days_now2['code'] != 'INC_RT' and days_now2['code'] != 'INC_MAT' and days_now2['code'] != 'WORK100':
                             new_worked_days.append({
                                 'name': days_now2['name'],
                                 'sequence': days_now2['sequence'],
                                 'code': days_now2['code'],
                                 'number_of_days': days_now2['number_of_days'],
                                 'number_of_hours': days_now2['number_of_hours'],
                                 'contract_id': days_now2['contract_id'],
                             })
                             new_days += days_now2['number_of_days']
                      if not self.reporte_asistencia:
                          for work_day_line in new_worked_days:
                               if work_day_line['code'] == 'WORK100':
                                    work_day_line.update({'number_of_days': self.dias_pagar - new_days,
                                                   'number_of_hours': (self.dias_pagar - new_days) * 8,
                                    })
                      _logger.info("new_worked_days %s, ", new_worked_days)

                   res = {
                       'employee_id': contract.employee_id.id,
                       'name': _('Nómina salarial de  %s para %s') % (contract.employee_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
                       'struct_id': self.estructura and self.estructura.id or contract.struct_id.id,
                       'contract_id': contract.id,
                       'payslip_run_id': self.id,
                       'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                       'worked_days_line_ids': [(0, 0, x) for x in new_worked_days], #slip_data['value'].get('worked_days_line_ids')]
                       'date_from': self.date_start,
                       'date_to': self.date_end,
                       'credit_note': self.credit_note,
                       'company_id': contract.company_id and contract.company_id.id,
                       #Added
                       'tipo_nomina' : self.tipo_nomina,
                       'fecha_pago' : self.fecha_pago,
                       'journal_id': self.journal_id.id,
                       'proyeccion':self.proyeccion,
                       'periodo_anterior':self.periodo_anterior.id,
                   }
                   if other_inputs and res.get('contract_id'):
                       contract_id = res.get('contract_id')
                       input_lines = list(other_inputs)
                       for line in input_lines:
                           line[2].update({'contract_id':contract_id})
                       #input_lines = map(lambda x: x[2].update({'contract_id':contract_id}),input_lines)
                       res.update({'input_line_ids': input_lines,})
                   res.update({'dias_pagar': self.dias_pagar,
                                   'imss_mes': self.imss_mes,
                                   'mes': '{:02d}'.format(self.date_end.month),
                                   'no_nomina': self.no_nomina,
                                   'isr_devolver': self.isr_devolver,
                                   'isr_ajustar': self.isr_ajustar,
                                   'isr_anual': self.isr_anual,
                                   'proyeccion' : self.proyeccion,
                                   'periodo_anterior' : self.periodo_anterior.id,
                                   'concepto_periodico': self.concepto_periodico})
                   employ_contract_id = self.env['hr.contract'].search([('id', '=', slip_data['value'].get('contract_id'))])
                   date_start_1 = employ_contract_id.date_start
                   d_from_1 = fields.Date.from_string(self.date_start)
                   d_to_1 = fields.Date.from_string(self.date_end)
                   if date_start_1:
                     if date_start_1 > d_from_1:
                        imss_dias =  (self.date_end - date_start_1).days + 1
                        res.update({'imss_dias': imss_dias,
                                  'dias_infonavit': imss_dias,})
                     else:
                         res.update({'imss_dias': self.imss_dias,})
                   else:
                      res.update({'imss_dias': self.imss_dias,})

                   payslips += self.env['hr.payslip'].create(res)

            return {'type': 'ir.actions.act_window_close'}

