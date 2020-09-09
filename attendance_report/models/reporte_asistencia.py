# -*- coding: utf-8 -*-

from odoo import fields, models, api , _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ReporteAsistencia(models.Model):
    _name = 'reporte.asistencia'

    fecha_inicial = fields.Date('Fecha inicial')
    fecha_final = fields.Date('Fecha final', store=True)
    asistencia_line_ids = fields.One2many('reporte.asistencia.line','report_asistencia_id',string="Reporte Asistencia lines")
    name = fields.Char("Name", required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    state = fields.Selection([('draft', 'Borrador'), ('done', 'Hecho'), ('cancel', 'Cancelado')], string='Estado', default='draft')
    periodo = fields.Selection(
        selection=[('semanal', 'Semanal'), 
                   ('quincenal', 'Quincenal'),
                   ('catorcenal', 'Catorcenal'),],
        string=_('Periodo'),
        default = 'semanal'
    )
    tipo_pago = fields.Selection(
        selection=[('01', 'Por periodo'), 
                   ('02', 'Por día'),],
        string=_('Conteo de días'),
    )
    #hr_dia= fields.Float(string='Horas Minimo Por Dia')
    #dia_laborado = fields.Float(string='Dia Laborado')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('reporte.asistencia') or '/'
       # vals['hr_dia'] = float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia'))
       # vals['dia_laborado'] = float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        result=super(ReporteAsistencia,self).create(vals)
        return result
       

    @api.onchange('fecha_inicial')
    def _get_fecha_final(self):
        if self.fecha_inicial:
            if self.periodo == 'semanal':
               self.fecha_final = fields.Date.from_string(self.fecha_inicial)  + timedelta(days=6)
            elif self.periodo == 'quincenal':
               self.fecha_final = fields.Date.from_string(self.fecha_inicial)  + timedelta(days=14)

    @api.model
    def default_get(self, fields):
        res = super(ReporteAsistencia, self).default_get(fields)

#        employee_ids = self.env['hr.employee'].search([('contract_ids.state','=','open')])
#        employees_id=[];
#        emp_added_ids = []
#        for employee in employee_ids:
#            if employee.id in emp_added_ids:
#                continue
#            employees_id.append((0,0,{'employee_id':employee.id}))
#            emp_added_ids.append(employee.id)
#        res['asistencia_line_ids'] = employees_id
        return res

#    @api.multi
    def action_validar(self):
        self.write({'state':'done'})
        return

#    @api.multi
    def action_cancelar(self):
        self.write({'state':'cancel'})

#    @api.multi
    def action_draft(self):
        self.write({'state':'draft'})

#     @api.multi
#     @api.onchange('fecha_inicial')
#     def set_all_employee(self):
#         if self.fecha_inicial:
#             employee_ids = self.env['hr.employee'].search([('contract_ids.state','=','open')])
#             repo_assi_obj=self.env['reporte.asistencia.line']
#             employees_id=[];
#             for employee in employee_ids:
#                 line =  repo_assi_obj.create({'employee_id':employee.id})
#                 employees_id.append(line.id)
#             list_set = set(employees_id)
#             employees_id = (list(list_set))      
#             self.asistencia_line_ids=employees_id   

#    @api.multi
    def calculate_attendance(self):
        if not self.fecha_inicial or not self.fecha_final:
            raise UserError(_('Falta seleccionar fecha inicial y final'))

        fecha_inicial = fields.Date.from_string(self.fecha_inicial)
        check_out = fields.Date.from_string(self.fecha_final)
        num_dias = int((check_out - fecha_inicial + timedelta(days=1)).days)
       # if self.periodo == 'quincenal' and self.tipo_pago == '01':
       #    num_dias = 15
        _logger.info('numdias %s', num_dias)
        employee_ids = self.env['hr.employee'].search([('contract_ids.state','=','open')])
        employees_id=[];
        emp_added_ids = []
        for employee in employee_ids:
            if employee.id in emp_added_ids:
                continue
            employees_id.append((0,0,{'employee_id':employee.id,'periodo':self.periodo,'tipo_pago':self.tipo_pago,'num_dias':num_dias}))
            #self.asistencia_line_ids.employee_id += employee
            emp_added_ids.append(employee.id)
        self.asistencia_line_ids = employees_id

        employees = self.asistencia_line_ids.mapped('employee_id')
        employees_ids = employees.ids
#         attendances = self.env['hr.attendance'].search([('name','>=', fecha_inicial),
#                                                         ('name','<=', end_date),
#                                                         ('employee_id','in', employees.ids)
#                                                         ])
        cr = self._cr
        if employees_ids:
            employees_ids = str(employees_ids)
            employees_ids = employees_ids[1:len(employees_ids)-1] 
            cr.execute("""select employee_id, sum(worked_hours), check_in::date from hr_attendance 
                        where check_in::date>='%s' and check_in::date <= '%s' and employee_id in (%s)
                        group by employee_id, check_in::date order by check_in::date 
                        """%(fecha_inicial.strftime(DEFAULT_SERVER_DATE_FORMAT), check_out.strftime(DEFAULT_SERVER_DATE_FORMAT), employees_ids))
            employee_data = cr.fetchall()
            employee_data_dict = {}
            for data in employee_data:
                employee_id = data[0]
                worked_hours = data[1]
                att_date = data[2]
                if employee_id not in employee_data_dict:
                    employee_data_dict.update({employee_id:{}})
                
                employee_data_dict[employee_id][att_date] = worked_hours
            days_dict = {'day_1':0, 'day_2':1, 'day_3':2, 'day_4':3, 'day_5': 4, 'day_6': 5, 'day_7': 6, 'day_8': 7, 'day_9': 8, 'day_10': 9, 'day_11': 10, 'day_12': 11, 'day_13': 12,
                         'day_14': 13, 'day_15': 14, 'day_16': 15}
            for line in self.asistencia_line_ids:
                employee_id = line.employee_id.id
                emp_data = employee_data_dict.get(employee_id)
                if emp_data:
                    vals = {}
                    for day_field, day in  days_dict.items():
                        day_date = fecha_inicial + relativedelta(days=day)
                        day_date = day_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                        if day_date in emp_data:
                            vals.update({day_field: emp_data[day_date]})
                    if vals:
                        line.write(vals)
        return True

class ReporteAsistenciaLine(models.Model):
    _name = 'reporte.asistencia.line'
    
    @api.model
    def _default_hr_dia(self):
        return float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia'))
        
#    @api.model
#    def _default_dia_laborado(self):
#        return float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
    
#    @api.model
#    def _default_periodo(self):
#        return self.env['ir.config_parameter'].sudo().get_param('attendance_report.periodo','semanal')
    
    hr_dia= fields.Float(string='Horas Minimo Por Dia', default=_default_hr_dia)
    num_dias = fields.Float(string='Numero de dias')

   # dia_laborado = fields.Float(string='Dia Laborado')
    
    periodo = fields.Selection(
        selection=[('semanal', 'Semanal'), 
                   ('quincenal', 'Quincenal'),
                   ('catorcenal', 'Catorcenal'),],
        string=_('Periodo'),
    )
    tipo_pago = fields.Selection(
        selection=[('01', 'Por periodo'), 
                   ('02', 'Por día'),],
        string=_('Conteo de días'),
    )

    report_asistencia_id = fields.Many2one('reporte.asistencia','Report Asistencia')
    employee_id = fields.Many2one('hr.employee','Empleado')
    day_1=fields.Float('D1')
    day_2=fields.Float('D2')
    day_3=fields.Float('D3')
    day_4=fields.Float('D4')
    day_5=fields.Float('D5')
    day_6=fields.Float('D6')
    day_7=fields.Float('D7')
    day_8=fields.Float('D8')
    day_9=fields.Float('D9')
    day_10=fields.Float('D10')
    day_11=fields.Float('D11')
    day_12=fields.Float('D12')
    day_13=fields.Float('D13')
    day_14=fields.Float('D14')
    day_15=fields.Float('D15')
    day_16=fields.Float('D16')
    dias_lab=fields.Float('Días', compute='_compute_dias_lab', store=True, readonly=True)

#    @api.one
    @api.depends('day_1', 'day_2', 'day_3', 'day_4', 'day_5', 'day_6', 'day_7','day_8', 'day_9', 'day_10', 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16')
    def _compute_dias_lab(self):
        falta = 0
        if self.day_1 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab +=float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_2 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_3 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_4 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_5 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_6 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_7 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_8 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_9 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_10 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_11 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_12 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_13 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            falta += 1
        if self.day_14 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            if self.num_dias > 14:
                falta += 1
        if self.day_15 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            if self.num_dias > 14:
                falta += 1
        if self.day_16 >= float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.horas_minimo_por_dia')):
            self.dias_lab += float(self.env['ir.config_parameter'].sudo().get_param('attendance_report.dia_laborado'))
        else:
            if self.num_dias > 14:
                falta += 1
        _logger.info('periodo %s --- tipo_pago %s', self.periodo, self.report_asistencia_id.tipo_pago)
        if self.report_asistencia_id.periodo == 'quincenal':
           if self.report_asistencia_id.tipo_pago == '01': # peridodo
              _logger.info('numdias2 %s --- dias lab --- falta', self.num_dias, self.dias_lab, falta)
              if self.num_dias == falta:
                  self.dias_lab = 0
              else:
                  self.dias_lab = 15 - falta
           #   if self.dias_lab > 15:
           #       self.dias_lab = 15
           #   if self.num_dias < 15 and self.dias_lab >= 13:
           #       self.dias_lab = 15
