# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
#from odoo.addons.hr_payroll.wizard.hr_payroll_payslips_by_employees import HrPayslipEmployees
from datetime import datetime, time, timedelta
import logging
_logger = logging.getLogger(__name__)

class HrPayslipEmployeesExt(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        payslip_batch = self.env['hr.payslip.run'].browse(active_id)
        struct_id = payslip_batch.estructura and payslip_batch.estructura.id or False
        other_inputs = []
        for other in payslip_batch.tabla_otras_entradas:
            if other.descripcion and other.codigo: 
                other_inputs.append((0,0,{'name':other.descripcion, 'code': other.codigo, 'amount':other.monto}))
        _logger.info('el de aplicaciones')

        run_data2 = self.env['hr.payslip.run'].search([('id', '=', active_id)])
        batch_last_id = run_data2.periodo_anterior
        #batch_last = self.env['hr.payslip.run'].search([('id', '=', batch_last_id.id)])
        _logger.info('entra a este')

        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            slip_data2 = self.env['hr.payslip'].onchange_employee_id(batch_last_id.date_start, batch_last_id.date_end, employee.id, contract_id=False)
            new_worked_days = []
            new_days = 0
            work_days_now = slip_data['value'].get('worked_days_line_ids')
            work_days_previous = slip_data2['value'].get('worked_days_line_ids')
            for days_now in work_days_now:
                  _logger.info('entra01')
                  if days_now['code'] == 'INC_EG' or days_now['code'] == 'INC_RT' or days_now['code'] == 'INC_MAT':
                       _logger.info('entra02')
                       new_worked_days.append({
                           'name': days_now['name'],
                           'sequence': days_now['sequence'],
                           'code': days_now['code'],
                           'number_of_days': days_now['number_of_days'],
                           'number_of_hours': days_now['number_of_hours'],
                           'contract_id': days_now['contract_id'],
                       })
                       new_days += days_now['number_of_days']
                  _logger.info('entra03')
            for days_now2 in work_days_previous:
                  _logger.info('entra04')
                  if days_now2['code'] != 'INC_EG' and days_now2['code'] != 'INC_RT' and days_now2['code'] != 'INC_MAT' and days_now2['code'] != 'WORK100':
                       _logger.info('entra05')
                       new_worked_days.append({
                           'name': days_now2['name'],
                           'sequence': days_now2['sequence'],
                           'code': days_now2['code'],
                           'number_of_days': days_now2['number_of_days'],
                           'number_of_hours': days_now2['number_of_hours'],
                           'contract_id': days_now2['contract_id'],
                       })
                       new_days += days_now2['number_of_days']
            _logger.info('escribe diaass')
            new_worked_days.append({
                           'name': "Días de trabajo",
                           'sequence': 1,
                           'code': 'WORK100',
                           'number_of_days': payslip_batch.dias_pagar - new_days,
                           'number_of_hours': (payslip_batch.dias_pagar - new_days) * 8,
                           'contract_id': slip_data['value'].get('contract_id'),
                       })
            _logger.info("new_worked_days %s, ", new_worked_days)
            
            # compute Prima vacacional en fecha correcta
            if employee.contract_id.tipo_prima_vacacional == '01':
                date_start = employee.contract_id.date_start
                if date_start:
                    d_from = fields.Date.from_string(from_date)
                    d_to = fields.Date.from_string(to_date)
                
                    date_start = fields.Date.from_string(date_start)
                    if datetime.today().year > date_start.year:
                        if str(date_start.day) == '29' and str(date_start.month) == '2':
                            date_start -=  datetime.timedelta(days=1)
                        date_start = date_start.replace(d_to.year)

                        if d_from <= date_start <= d_to:
                            day_to = datetime.combine(fields.Date.from_string(to_date), time.max)
                            diff_date = day_to - datetime.combine(employee.contract_id.date_start, time.max)
                            years = diff_date.days /365.0
                            antiguedad_anos = int(years)
                            tabla_antiguedades = employee.contract_id.tablas_cfdi_id.tabla_antiguedades.filtered(lambda x: x.antiguedad <= antiguedad_anos)
                            tabla_antiguedades = tabla_antiguedades.sorted(lambda x:x.antiguedad, reverse=True)
                            vacaciones = tabla_antiguedades and tabla_antiguedades[0].vacaciones or 0
                            prima_vac = tabla_antiguedades and tabla_antiguedades[0].prima_vac or 0
                            attendances = {
                                        'name': 'Prima vacacional',
                                        'sequence': 2,
                                        'code': 'PVC',
                                        'number_of_days': vacaciones * prima_vac / 100.0,
                                        'number_of_hours': vacaciones * prima_vac / 100.0 * 8,
                                        'contract_id': employee.contract_id.id,
                            }
                            new_worked_days.append(attendances)

            # compute Prima vacacional
            if employee.contract_id.tipo_prima_vacacional == '03':
                date_start = employee.contract_id.date_start
                if date_start:
                    d_from = fields.Date.from_string(from_date)
                    d_to = fields.Date.from_string(to_date)

                    date_start = fields.Date.from_string(date_start)
                    if datetime.today().year > date_start.year and d_from.day > 15:
                        if str(date_start.day) == '29' and str(date_start.month) == '2':
                            date_start -=  datetime.timedelta(days=1)
                        date_start = date_start.replace(d_to.year)
                        d_from = d_from.replace(day=1)

                        if d_from <= date_start <= d_to:
                            day_to = datetime.combine(fields.Date.from_string(to_date), time.max)
                            diff_date = day_to - datetime.combine(employee.contract_id.date_start, time.max)
                            years = diff_date.days /365.0
                            antiguedad_anos = int(years)
                            tabla_antiguedades = employee.contract_id.tablas_cfdi_id.tabla_antiguedades.filtered(lambda x: x.antiguedad <= antiguedad_anos)
                            tabla_antiguedades = tabla_antiguedades.sorted(lambda x:x.antiguedad, reverse=True)
                            vacaciones = tabla_antiguedades and tabla_antiguedades[0].vacaciones or 0
                            prima_vac = tabla_antiguedades and tabla_antiguedades[0].prima_vac or 0
                            attendances = {
                                        'name': 'Prima vacacional',
                                        'sequence': 2,
                                        'code': 'PVC',
                                        'number_of_days': vacaciones * prima_vac / 100.0,
                                        'number_of_hours': vacaciones * prima_vac / 100.0 * 8,
                                        'contract_id': employee.contract_id.id,
                            }
                            new_worked_days.append(attendances)

            # compute Prima dominical
            if employee.contract_id.prima_dominical:
                domingos = 0
                d_from = fields.Date.from_string(from_date)
                d_to = fields.Date.from_string(to_date)
                for i in range((d_to - d_from).days + 1):
                           if (d_from + datetime.timedelta(days=i+1)).weekday() == 0:
                               domingos = domingos + 1
                attendances = {
                                   'name': 'Prima dominical',
                                   'sequence': 2,
                                   'code': 'PDM',
                                   'number_of_days': domingos,
                                   'number_of_hours': domingos * 8,
                                   'contract_id': employee.contract_id.id,
                }
                new_worked_days.append(attendances)
          #  work_days_ids = self.env['hr.payslip.work_days'].search([('id', '=', work_days)])
          #  for work in work_days_ids:
          #       _logger.info("codigo %s, dias %s", work.name, work.code)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': struct_id or slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in new_worked_days], #slip_data['value'].get('worked_days_line_ids')]
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
                #Added
                'tipo_nomina' : payslip_batch.tipo_nomina,
                'fecha_pago' : payslip_batch.fecha_pago,
                'journal_id': payslip_batch.journal_id.id,
                'proyeccion':payslip_batch.proyeccion,
                'periodo_anterior':payslip_batch.periodo_anterior.id,
            }
            if other_inputs and res.get('contract_id'):
                contract_id = res.get('contract_id')
                input_lines = list(other_inputs)
                for line in input_lines:
                    line[2].update({'contract_id':contract_id})
                #input_lines = map(lambda x: x[2].update({'contract_id':contract_id}),input_lines)
                res.update({'input_line_ids': input_lines,})
            res.update({'dias_pagar': payslip_batch.dias_pagar,
                            #'imss_dias': payslip_batch.imss_dias,
                            'imss_mes': payslip_batch.imss_mes,
                            'ultima_nomina': payslip_batch.ultima_nomina,
                            'mes': '{:02d}'.format(to_date.month),
                            'isr_devolver': payslip_batch.isr_devolver,
                            'isr_ajustar': payslip_batch.isr_ajustar,
                            'isr_anual': payslip_batch.isr_anual,
                            'proyeccion' : payslip_batch.proyeccion,
                            'periodo_anterior' : payslip_batch.periodo_anterior.id,
                            'concepto_periodico': payslip_batch.concepto_periodico})
            employ_contract_id = self.env['hr.contract'].search([('id', '=', slip_data['value'].get('contract_id'))])
            date_start_1 = employ_contract_id.date_start
            d_from_1 = fields.Date.from_string(from_date)
            d_to_1 = fields.Date.from_string(to_date)
            if date_start_1:
               if date_start_1 > d_from_1:
                  imss_dias =  (to_date - date_start_1).days + 1
                  res.update({'imss_dias': imss_dias,
                           'dias_infonavit': imss_dias,})
               else:
                  res.update({'imss_dias': payslip_batch.imss_dias,})
            else:
               res.update({'imss_dias': payslip_batch.imss_dias,})

            payslips += self.env['hr.payslip'].create(res)

        payslips.compute_sheet()
        
        return {'type': 'ir.actions.act_window_close'}

