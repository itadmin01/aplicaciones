# -*- coding: utf-8 -*-

from odoo import models, fields, api
#import time
#from datetime import datetime
#from dateutil import relativedelta
from datetime import datetime, timedelta

from collections import defaultdict
import io
from odoo.tools.misc import xlwt
import base64
#import logging
#_logger = logging.getLogger(__name__)

class CalculoSBC(models.TransientModel):
    _name = 'wizard.sbc.bimestral'
    _description = 'CalculoSBC'

    name = fields.Char("Name")
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    bimestre =  fields.Selection(
        selection=[('1', 'Primero'), 
                   ('2', 'Segundo'),
                   ('3', 'Tercero'),
                   ('4', 'Cuarto'),
                   ('5', 'Quinto'),
                   ('6', 'Sexto'),],
        string='Bimestre', required=True, default='1'
    )
    tabla_cfdi = fields.Many2one('tablas.cfdi','Tabla CFDI')
    date_from = fields.Date(string='Fecha inicio')
    date_to = fields.Date(string='Fecha fin')
    registro_patronal = fields.Char(string='Registro patronal')
    file_data = fields.Binary("File Data")

    def print_sbc_report(self):
        domain=[('state','=', 'done')]
        tablas_bimestre = self.tabla_cfdi.tabla_bimestral
        fecha_bimestre = tablas_bimestre[int(self.bimestre) -1]

        self.date_from = fecha_bimestre.dia_inicio
        domain.append(('date_from','>=',self.date_from))
        self.date_to = fecha_bimestre.dia_fin
        domain.append(('date_to','<=',self.date_to))
        primer_dia = self.date_to.replace(day=1)

        if self.employee_id:
            domain.append(('employee_id','=',self.employee_id.id))
        #if not self.employee_id and self.department_id:
        #    employees = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
        #    domain.append(('employee_id','in',employees.ids))

        payslips = self.env['hr.payslip'].search(domain)
        rules = self.env['hr.salary.rule'].search([('variable_imss', '=', True)])
        payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
        
        workbook = xlwt.Workbook()
        bold = xlwt.easyxf("font: bold on;")
        
        worksheet = workbook.add_sheet('Nomina')
        
        from_to_date = 'De  %s a %s'%(self.date_from or '', self.date_to or '')
        concepto = 'Concepto:  %s'%(self.date_from)
        
        worksheet.write_merge(1, 1, 0, 4, 'Reporte de cálculo de sueldo base de cotización', bold)
        worksheet.write_merge(2, 2, 0, 4, from_to_date, bold)
        #worksheet.write_merge(3, 3, 0, 4, concepto, bold)
        
        worksheet.write(4, 0, 'Empleado', bold)
        worksheet.write(4, 1, 'NSS', bold)
        worksheet.write(4, 2, 'RFC', bold)
        worksheet.write(4, 3, 'CURP', bold)
        worksheet.write(4, 4, 'Fecha de alta', bold)
        worksheet.write(4, 5, 'Departamento', bold)
        worksheet.write(4, 6, 'Sueldo diario', bold)
        worksheet.write(4, 7, 'Factor aguinaldo', bold)
        worksheet.write(4, 8, 'Aguinaldo diario', bold)
        worksheet.write(4, 9, 'Fecha', bold)
        worksheet.write(4, 10, 'Dias de antiguedad', bold)
        worksheet.write(4, 11, 'Antiguedad en años', bold)
        worksheet.write(4, 12, 'Vacaciones', bold)
        worksheet.write(4, 13, 'Prima vacacional 25%', bold)
        worksheet.write(4, 14, 'Prima vacacional año', bold)
        worksheet.write(4, 15, 'Prima vacacional x dia', bold)
        worksheet.write(4, 16, 'SDI fijo', bold)
        worksheet.write(4, 18, 'Dias de salario devengado', bold)
        col = 23
        num_rules = 0
        rule_index = {}
        for rule in rules:
            worksheet.write(4, col, 'Total ' + rule.name, bold)
            worksheet.write(4, col+1, 'Exento ' + rule.name, bold)
            worksheet.write(4, col+2, 'Gravado ' + rule.name, bold)
            rule_index.update({rule.id:col})
            col +=3
            num_rules += 1

        tot_col = 23 + num_rules * 3 + 1
        worksheet.write(4, tot_col, 'Variable Bimestral', bold)
        worksheet.write(4, tot_col+1, 'Variable diario', bold)
        worksheet.write(4, tot_col+2, 'SBC', bold)
        #employees = defaultdict(dict)
        #employee_payslip = defaultdict(set)
        employees = {}
        for line in payslip_lines:
            if line.slip_id.employee_id not in employees:
                employees[line.slip_id.employee_id] = {line.slip_id: []}
            if line.slip_id not in employees[line.slip_id.employee_id]:
                employees[line.slip_id.employee_id].update({line.slip_id: []})
            employees[line.slip_id.employee_id][line.slip_id].append(line)
            
            #employees[line.slip_id.employee_id].add(line)
            
            #employee_payslip[line.slip_id.employee_id].add(line.slip_id)
            
        row = 5
        tipo_nomina = {'O':'Nómina ordinaria', 'E':'Nómina extraordinaria'}
        for employee, payslips in employees.items():
            init_row = row
            total_gravado = 0
            dias_periodo = 0
            contrato = employee.contract_id[0]
            factor_aguinaldo = 15*1/366
            aguinaldo = contrato.sueldo_diario * factor_aguinaldo
            dia_hoy =  self.date_to + timedelta(days=1)
            dias_antiguedad = dia_hoy - contrato.date_start + timedelta(days=1)
            dias_anos = dias_antiguedad.days / 366
            if dias_anos < 1.0: 
                tablas_cfdi_lines = contrato.tablas_cfdi_id.tabla_antiguedades.filtered(lambda x: x.antiguedad >= dias_anos).sorted(key=lambda x:x.antiguedad) 
            else: 
                tablas_cfdi_lines = contrato.tablas_cfdi_id.tabla_antiguedades.filtered(lambda x: x.antiguedad <= dias_anos).sorted(key=lambda x:x.antiguedad, reverse=True) 
            tablas_cfdi_line = tablas_cfdi_lines[0]
            dias_pv = tablas_cfdi_line.vacaciones * tablas_cfdi_line.prima_vac/100.0
            monto_pv = dias_pv * contrato.sueldo_diario
            pv_x_dia = monto_pv / 366
            sdi = contrato.sueldo_diario + aguinaldo + pv_x_dia
            uma = contrato.tablas_cfdi_id.uma * 30
            msbc = contrato.sueldo_base_cotizacion * 30
            worksheet.write(row, 0, employee.name)
            worksheet.write(row, 1, employee.segurosocial)
            worksheet.write(row, 2, employee.rfc)
            worksheet.write(row, 3, employee.curp)
            worksheet.write(row, 4, contrato.date_start)
            worksheet.write(row, 5, contrato.department_id.name)
            worksheet.write(row, 6, contrato.sueldo_diario)
            worksheet.write(row, 7, round(factor_aguinaldo,2))
            worksheet.write(row, 8, round(aguinaldo,2))
            worksheet.write(row, 9, dia_hoy)
            worksheet.write(row, 10, dias_antiguedad.days)
            worksheet.write(row, 11, round(dias_anos,2))
            worksheet.write(row, 12, tablas_cfdi_line.vacaciones)
            worksheet.write(row, 13, dias_pv)
            worksheet.write(row, 14, round(monto_pv,2))
            worksheet.write(row, 15, round(pv_x_dia,2))
            worksheet.write(row, 16, round(sdi,2))
            row +=1
            worksheet.write(row, 20, 'Fecha de la nomina', bold)
            worksheet.write(row, 21, 'Tipo', bold)
            worksheet.write(row, 22, 'Dias laborados', bold)
            row +=1
            total_by_rule = defaultdict(lambda: 0.0)
            total_by_rule1 = defaultdict(lambda: 0.0)
            total_by_rule2 = defaultdict(lambda: 0.0)
            for payslip,lines in payslips.items():
                worksheet.write(row, 20, payslip.date_from)
                worksheet.write(row, 21, tipo_nomina.get(payslip.tipo_nomina,''))
                #dias laborados
                dias_lab = 0
                if payslip.tipo_nomina == 'O':
                   for workline in payslip.worked_days_line_ids:
                       if workline.code == 'WORK100' or workline.code == 'FJC':
                           dias_periodo += workline.number_of_days
                           dias_lab += workline.number_of_days
                worksheet.write(row, 22, dias_lab)

                for line in lines:
                    worksheet.write(row, rule_index.get(line.salary_rule_id.id), line.total)
                    total_by_rule[line.salary_rule_id.id] += line.total
                    if payslip.date_to < primer_dia:
                        total_by_rule1[line.salary_rule_id.id] += line.total
#                        _logger.info("total1: %s", total_by_rule1[line.salary_rule_id.id])
                    else:
                        total_by_rule2[line.salary_rule_id.id] += line.total
#                        _logger.info("total2: %s", total_by_rule2[line.salary_rule_id.id])
                row +=1

            #worksheet.write(row, 19, 'Total', bold)
            for rule_id, total in total_by_rule.items():
                worksheet.write(init_row, rule_index.get(rule_id), total)
                #sacamos calculo exento y grvado dependiendo de opción en regla salarial
                regla = self.env['hr.salary.rule'].search([('id', '=', rule_id)])
                if regla.variable_imss_tipo == '001':  # Monto total
                   worksheet.write(init_row, rule_index.get(rule_id)+1, 0)
                   worksheet.write(init_row, rule_index.get(rule_id)+2, total)
                   total_gravado  += total
                elif regla.variable_imss_tipo == '002': # Pct de UMA
                   tot_exento = uma * regla.variable_imss_monto/100
                   bimestre_exento = 0
                   bimestre_gravado = 0
                   if total_by_rule1[rule_id]:   #### calcula exento y gravado para primer mes
                        if total_by_rule1[rule_id] > tot_exento:
                           total_gravado  += total_by_rule1[rule_id]-tot_exento
                           bimestre_gravado += total_by_rule1[rule_id]-tot_exento
                           bimestre_exento += tot_exento
                        else:
                           bimestre_exento += total_by_rule1[rule_id]
                   if total_by_rule2[rule_id]:  #### calcula exento y gravado para segundo mes
                        if total_by_rule2[rule_id] > tot_exento:
                           total_gravado  += total_by_rule2[rule_id]-tot_exento
                           bimestre_gravado += total_by_rule2[rule_id]-tot_exento
                           bimestre_exento += tot_exento
                        else:
                           bimestre_exento += total_by_rule2[rule_id]
                   worksheet.write(init_row, rule_index.get(rule_id)+1, bimestre_exento)
                   worksheet.write(init_row, rule_index.get(rule_id)+2, bimestre_gravado)
                else:   # Pct de SBC
                   tot_exento = msbc * regla.variable_imss_monto/100
                   bimestre_exento = 0
                   bimestre_gravado = 0
                   if total_by_rule1[rule_id]:   #### calcula exento y gravado para primer mes
                        if total_by_rule1[rule_id] > tot_exento:
                           total_gravado  += total_by_rule1[rule_id]-tot_exento
                           bimestre_gravado += total_by_rule1[rule_id]-tot_exento
                           bimestre_exento += tot_exento
                        else:
                           bimestre_exento += total_by_rule1[rule_id]
                   if total_by_rule2[rule_id]:  #### calcula exento y gravado para segundo mes
                        if total_by_rule2[rule_id] > tot_exento:
                           total_gravado  += total_by_rule2[rule_id]-tot_exento
                           bimestre_gravado += total_by_rule2[rule_id]-tot_exento
                           bimestre_exento += tot_exento
                        else:
                           bimestre_exento += total_by_rule2[rule_id]
                   worksheet.write(init_row, rule_index.get(rule_id)+1, bimestre_exento)
                   worksheet.write(init_row, rule_index.get(rule_id)+2, bimestre_gravado)
            #poner totales
            worksheet.write(init_row, 18, dias_periodo)
            worksheet.write(init_row, tot_col, total_gravado)
            worksheet.write(init_row, tot_col+1, round(total_gravado/dias_periodo,2))
            worksheet.write(init_row, tot_col+2, round(sdi + total_gravado/dias_periodo,2))
            row +=1
                

                
        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        
        self.write({'file_data':base64.b64encode(data)})
        action = {
            'name': 'Payslips',
            'type': 'ir.actions.act_url',
            'url': "/web/content/?model="+self._name+"&id=" + str(self.id) + "&field=file_data&download=true&filename=sbc_bimestral.xls",
            'target': 'self',
            }
        return action
        
    
    