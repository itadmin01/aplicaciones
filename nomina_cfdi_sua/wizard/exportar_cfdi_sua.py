
from odoo import models, fields, api,_
import base64
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, Warning
import logging
_logger = logging.getLogger(__name__)

class exportar_cfdi_sua(models.TransientModel):
    _name = 'exportar.cfdi.sua'
    
    start_date = fields.Date('Fecha inicio')
    end_date = fields.Date('Fecha fin')
    employee_id = fields.Many2one("hr.employee",'Empleado')
    file_content = fields.Binary("Archivo")
    tipo_exp_sua = fields.Selection(
        selection=[('0', 'Ausentismo'),
                   ('1', 'Incapacidad'),
                   ('2', 'Alta / Reingreso'),
                   ('3', 'Baja'),
                   ('4', 'Cambio sueldo'),],
        string='Tipo exportación',
    )
    tipo_exp_idse = fields.Selection(
        selection=[('0', 'Alta / Reingreso'),
                   ('1', 'Baja'),
                   ('2', 'Cambio sueldo'),],
        string='Tipo exportación',
    )
    

    def print_exportar_cfdi_sua(self):
        file_text = []
        is_idse = self._context.get('idse')
        
        domain = [('fecha','>=',self.start_date),('fecha','<=',self.end_date)]
        domain2 = [('fecha_inicio','>=',self.start_date),('fecha_inicio','<=',self.end_date)]
        domain.append(('state','=', 'done'))
        domain2.append(('state','=', 'done'))
        if self.employee_id:
            domain.append(('employee_id','=', self.employee_id.id))
            domain2.append(('employee_id','=', self.employee_id.id))
        ################ EXPORTACIÓN A IDSE #############################
        if is_idse:
            domain.append(('tipo_de_incidencia', '!=','Cambio reg. patronal'))
            f_nomina = []
            in_nomina = []
        ################ EXPORTACIÓN A SUA #############################
        else:
            f_nomina = self.env['faltas.nomina'].search(domain2)
            in_nomina = self.env['incapacidades.nomina'].search(domain)
        i_nomina = self.env['incidencias.nomina'].search(domain)

        ################ EXPORTACIÓN A IDSE #############################
        if is_idse:
            for rec in i_nomina:
                #INDICATES THE MOVEMENT TYPE OF THE INCIDENCIA
                if self.tipo_exp_idse == '0': #Alta / Reingreso
                   if rec.tipo_de_incidencia=='Reingreso' or rec.tipo_de_incidencia=='Alta':
                    employee = rec.employee_id
                    data1 = employee.registro_patronal[0:11] or '           ' #Registro Patronal
                    data3= employee.segurosocial[0:11] or '           ' #Número de seguridad social
                    data5 = employee.apellido_Paterno.ljust(27, ' ') or '                           ' #Primer apellido
                    data6 = employee.apellido_Materno.ljust(27, ' ') or '                           ' #Segundo apellido
                    data7 = employee.nombreEmpleado.ljust(27, ' ') or '                           ' #Nombre(s)
                    data8 = '{:06d}'.format(int(round(employee.contract_id.sueldo_base_cotizacion,2)*100)) or '      ' #Salario base de cotización
                    data9 = '      ' #Filler
                    data10 = employee.tipoDeTrabajador or '' #Tipo de trabajador
                    data11 = employee.tipoDeSalario or '' #Tipo de salario
                    data12 = employee.tipoDeJornada or '' #Semana o jornada reducida
                    data13 = rec.fecha.strftime("%d%m%Y") #Fecha de movimiento (inicio de labores)
                    data14 = employee.unidadMedicina[0:3] or '' #Unidad de medicina familiar
                    data15 = '  ' #Filler
                    data16 = '08' #Tipo de movimiento
                    data17 = employee.no_guia[0:3].ljust(5, ' ') or '' #Guía
                    data18 = employee.no_empleado.ljust(10, ' ') or '' # número de empleado
                    data19 = ' ' #Filler
                    data20 = employee.curp.rjust(18, ' ') #Clave única de registro de población
                    data21 = '9' #Identificador
                    file_text.append((data1)+(data3)+(data5)+(data6)+(data7)+(data8)+(data9)+(data10)
                    +(data11)+(data12)+(data13)+(data14)+(data15)+(data16)+(data17)+(data18)+(data19)+(data20)+(data21))

                if self.tipo_exp_idse == '1': #Baja
                   if rec.tipo_de_incidencia=='Baja':
                    employee = rec.employee_id
                    data1 = employee.registro_patronal[0:11] or '           ' #Registro Patronal
                    data2= employee.segurosocial[0:11] or '           ' #Número de seguridad social
                    data3 = employee.apellido_Paterno.ljust(27, ' ') or '                           ' #Primer apellido
                    data4 = employee.apellido_Materno.ljust(27, ' ') or '                           ' #Segundo apellido
                    data5 = employee.nombreEmpleado.ljust(27, ' ') or '                           ' #Nombre(s)
                    data6 = '000000000000000' #Filler
                    data7 = rec.fecha.strftime("%d%m%Y") #Fecha de movimiento (fecha de baja)
                    data8 = '     ' #Filler
                    data9 = '02' #Tipo de movimiento
                    data10 = employee.no_guia[0:3].ljust(5, ' ') or '' # Guía
                    data11 = employee.no_empleado.ljust(10, ' ') or ''# número de empleado
                    data12 = rec.tipo_de_baja or '' #Tipo de baja
                    data13 = '                  ' #Filler
                    data14 = '9' #Identificador
                    file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data6)+(data7)+(data8)+(data9)+(data10)
                    +(data11)+(data12)+(data13)+(data14))

                if self.tipo_exp_idse == '2': #Cambio salario
                   if rec.tipo_de_incidencia=='Cambio salario':
                    employee = rec.employee_id
                    data1 = employee.registro_patronal[0:11] or '           ' #Registro Patronal
                    data2= employee.segurosocial[0:11] or '           ' #Número de seguridad social
                    data3 = employee.apellido_Paterno.ljust(27, ' ') or '                           ' #Primer apellido
                    data4 = employee.apellido_Materno.ljust(27, ' ') or '                           ' #Segundo apellido
                    data5 = employee.nombreEmpleado.ljust(27, ' ') or '                           ' #Nombre(s)
                    data6 = '{:06d}'.format(int(round(employee.contract_id.sueldo_base_cotizacion,2)*100)) or '      ' #Salario base de cotización
                    data7 = '       ' #Filler
                    data8 = employee.tipoDeSalario or '' #Tipo de salario
                    data9 = employee.tipoDeJornada or '' #Semana o jornada reducida
                    data10 = rec.fecha.strftime("%d%m%Y") #Fecha de movimiento (inicio de labores)
                    data11 = '     ' #Filler
                    data12 = '07' #Tipo de movimiento
                    data13 = employee.no_guia[0:3].ljust(5, ' ') or '' # Guía
                    data14 = employee.no_empleado.ljust(10, ' ') or '' # número de empleado
                    data15 = ' ' #Filler
                    data16 = employee.curp.rjust(18, ' ') #Clave única de registro de población
                    data17 = '9' #Identificador
                    file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data6)+(data7)+(data8)+(data9)+(data10)
                    +(data11)+(data12)+(data13)+(data14)+(data15)+(data16)+(data17))

        ################ EXPORTACIÓN A SUA #############################
        else:
            if self.tipo_exp_sua == '0': ##Tipo ausentismo
               for rec in f_nomina:
                   if rec.tipo_de_falta != 'Justificada con goce de sueldo':
                      employee = rec.employee_id
                      data3 = '11'
                      data4=''
                      if rec.fecha_inicio:
                          data4 = rec.fecha_inicio.strftime("%d%m%Y")
                      data7 = ''
                      folioimss = '        '
                      #if employee.contract_id:
                      data7='0000000' #'{:07d}'.format(int(employee.contract_id.sueldo_diario_integrado*100))
                      file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '           ')+(data3)+(data4)+(folioimss)+'{:02d}'.format(rec.dias)+data7)

            if self.tipo_exp_sua == '1': ##Tipo Incapacidad
               for rec in in_nomina:
                   employee = rec.employee_id
                   data3 = '12'
                   data4=''

                   if rec.fecha:
                       data4 = rec.fecha.strftime("%d%m%Y")
                   data7 = ''
                   #if employee.contract_id:
                   data7='0000000' #'{:07d}'.format(int(employee.contract_id.sueldo_diario_integrado*100)) 
                   file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '')+(data3)+(data4)+(rec.folio_incapacidad[0:8])+'{:02d}'.format(rec.dias)+data7)

            if self.tipo_exp_sua == '2':  ##Tipo reingreso
               for rec in i_nomina:
                   if rec.tipo_de_incidencia=='Reingreso' or rec.tipo_de_incidencia=='Alta':
                      employee = rec.employee_id
                      data3 = '08'
                      data4=''
                      if rec.fecha:
                          data4 = rec.fecha.strftime("%d%m%Y")
                      data7 = '0000000'
                      folioimss = '        '
                      diasincidencia = '00'
                      if employee.contract_id:
                          data7='{:07d}'.format(int(round(employee.contract_id.sueldo_diario_integrado,2)*100))
                      file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '           ')+(data3)+(data4)+(folioimss)+(diasincidencia)+data7)

            if self.tipo_exp_sua == '3':  ##Tipo baja
               for rec in i_nomina:
                   if rec.tipo_de_incidencia=='Baja':
                      employee = rec.employee_id
                      data3 = '02'
                      data4=''
                      if rec.fecha:
                          data4 = rec.fecha.strftime("%d%m%Y")
                      data7 = '0000000'
                      folioimss = '        '
                      diasincidencia = '00'
                      file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '           ')+(data3)+(data4)+(folioimss)+(diasincidencia)+data7)

            if self.tipo_exp_sua == '4':  ##Tipo cambio de sueldo
               for rec in i_nomina:
                   if rec.tipo_de_incidencia=='Cambio salario':
                      employee = rec.employee_id
                      data3 = '07'
                      data4=''
                      if rec.fecha:
                          data4 = rec.fecha.strftime("%d%m%Y")
                      data7 = '0000000'
                      folioimss = '        '
                      diasincidencia = '00'
                      if employee.contract_id:
                          data7='{:07d}'.format(int(round(employee.contract_id.sueldo_diario_integrado,2)*100))
                      file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '           ')+(data3)+(data4)+(folioimss)+(diasincidencia)+data7)

        if not file_text:
            raise UserError(_("No hay datos para generar el archivo."))
        
        file_text = '\n'.join(file_text)
        file_text = file_text.encode()
        filename = datetime.now().strftime("%y%m-%d%H%M%S")+'.txt'
        self.write({'file_content':base64.b64encode(file_text)})
        return {
                'type' : 'ir.actions.act_url',
                'url': "/web/content/?model="+self._name+"&id=" + str(self.id) + "&field=file_content&download=true&filename="+filename+'&mimetype=text/plain',
                'target':'self',
                }
        
