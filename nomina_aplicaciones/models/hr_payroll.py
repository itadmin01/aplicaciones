# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    dias_laborados = fields.Boolean(string='Dias laborados')
    otras_entradas = fields.Boolean(string='Otras entradas')

class HrPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ['hr.payslip','mail.thread']

    isr_proyectado = fields.Float('ISR proyectado', default=0)
    percepcion_gravada_proyectado = fields.Float('Percepción gravada', default=0)
    proyeccion = fields.Boolean(string='Proyeccion')
    gratificacion = fields.Boolean(string='Gratificacion')

    def proyectado(self):
       perc1 = self.percepciones_gratificacion()
       isr1 = self.compute_isr(perc1)
       perc2 = self.percepciones_dic()
       isr2 = self.compute_isr(perc2)
       if self.gratificacion:
          self.isr_proyectado = isr1 + isr2
          self.percepcion_gravada_proyectado = perc1 + perc2
       else:
          self.isr_proyectado = isr2
          self.percepcion_gravada_proyectado = perc2

    def percepciones_gratificacion(self):
       #leer tablas
       total_percepciones = self.contract_id.sueldo_diario * 15

       return total_percepciones

    def percepciones_dic(self):
       #leer tablas
       total_percepciones = self.contract_id.sueldo_diario * 16
       total_percepciones += self.contract_id.bono_asistencia_amount + self.contract_id.bono_puntualidad_amount

       return total_percepciones

    def compute_isr(self, percepciones_gravadas):
       #leer tablas
       limite_inferior = 0
       cuota_fija = 0
       porcentaje_sobre_excedente = 0
       subsidio_empleo = 0
       dias_pagar = 0
       grabado_mensual = 0

       #dias laborados
       if self.contract_id.periodicidad_pago == '02':
            dias_pagar =  7
       elif self.contract_id.periodicidad_pago == '04':
            dias_pagar =  15

       #grabado_mensual
       grabado_mensual = percepciones_gravadas / dias_pagar * self.contract_id.tablas_cfdi_id.imss_mes

       if self.contract_id.tablas_cfdi_id:
           line = self.env['tablas.general.line'].search([('form_id','=',self.contract_id.tablas_cfdi_id.id),('lim_inf','<=',grabado_mensual)],order='lim_inf desc',limit=1)
           if line:
              limite_inferior = line.lim_inf
              cuota_fija = line.c_fija
              porcentaje_sobre_excedente = line.s_excedente
           line2 = self.env['tablas.subsidio.line'].search([('form_id','=',self.contract_id.tablas_cfdi_id.id),('lim_inf','<=',grabado_mensual)],order='lim_inf desc',limit=1)
           if line2:
              subsidio_empleo = line2.s_mensual

       #articulo 113
       excedente_limite_superior = grabado_mensual - limite_inferior
       impuesto_marginal = excedente_limite_superior * porcentaje_sobre_excedente/100
       isr_tarifa_113 = impuesto_marginal + cuota_fija

       #subsidio mensual
       subsidio_pagado = isr_tarifa_113 - subsidio_empleo
       total = (isr_tarifa_113 / self.contract_id.tablas_cfdi_id.imss_mes) * dias_pagar
       total2 =  (subsidio_pagado / self.contract_id.tablas_cfdi_id.imss_mes) * dias_pagar

       result = 0
       if subsidio_pagado < 0:
            result =  0
       else:
            if total2 < 0:
               result = abs(total)
            else:
               result = abs(total2)
       return result
