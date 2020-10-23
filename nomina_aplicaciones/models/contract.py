# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
#import datetime
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class Contract(models.Model):
    _inherit = "hr.contract"

    @api.model
    def calculate_sueldo_base_cotizacion(self): 
        if self.date_start: 
            today = datetime.today().date()
            diff_date = (today - self.date_start + timedelta(days=1)).days
            years = diff_date /365.0
            #_logger.info('years ... %s', years)
            tablas_cfdi = self.tablas_cfdi_id 
            if not tablas_cfdi: 
                tablas_cfdi = self.env['tablas.cfdi'].search([],limit=1) 
            if not tablas_cfdi:
                return 
            if years < 1.0: 
                tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad >= years).sorted(key=lambda x:x.antiguedad) 
            else: 
                tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad <= years).sorted(key=lambda x:x.antiguedad, reverse=True) 
            if not tablas_cfdi_lines: 
                return 
            tablas_cfdi_line = tablas_cfdi_lines[0]
            max_sdi = tablas_cfdi.uma * 25
            sdi = self.wage/30.0 + 0.041 * self.wage/30.0 + ((tablas_cfdi_line.vacaciones)* 0.25 * self.wage/30.0) / 366
            if sdi > max_sdi:
                sueldo_base_cotizacion = max_sdi
            else:
                sueldo_base_cotizacion = sdi
        else: 
            sueldo_base_cotizacion = 0
        return sueldo_base_cotizacion

    @api.model
    def calculate_sueldo_diario_integrado(self): 
        if self.date_start: 
            today = datetime.today().date()
            diff_date = (today - self.date_start + timedelta(days=1)).days
            years = diff_date /365.0
            #_logger.info('years ... %s', years)
            tablas_cfdi = self.tablas_cfdi_id 
            if not tablas_cfdi: 
                tablas_cfdi = self.env['tablas.cfdi'].search([],limit=1) 
            if not tablas_cfdi:
                return 
            if years < 1.0: 
                tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad >= years).sorted(key=lambda x:x.antiguedad) 
            else: 
                tablas_cfdi_lines = tablas_cfdi.tabla_antiguedades.filtered(lambda x: x.antiguedad <= years).sorted(key=lambda x:x.antiguedad, reverse=True) 
            if not tablas_cfdi_lines: 
                return 
            tablas_cfdi_line = tablas_cfdi_lines[0]
            max_sdi = tablas_cfdi.uma * 25
            sdi = self.wage/30.0 + 0.041 * self.wage/30.0 + ((tablas_cfdi_line.vacaciones)* 0.25 * self.wage/30.0) / 366
            sueldo_diario_integrado = sdi
        else: 
            sueldo_diario_integrado = 0
        return sueldo_diario_integrado

    @api.onchange('wage')
    def compute_vale_despensa(self):
        total = 0
        if self.wage and self.tablas_cfdi_id:
            exento = self.tablas_cfdi_id.imss_mes * self.tablas_cfdi_id.uma*10
            if self.wage < 13500:
                if self.job_id.name == 'Operador de Tienda' or self.job_id.name == 'Gerente de Sucursal':
                    total = self.wage * 0.10
                else:
                    total = 1350
            elif self.wage > 13500 and self.wage < 26409:
                total = self.wage * 0.10
            elif self.wage > 26409:
                total = 2641
        values = {
            'vale_despensa_amount': total,
            }
        self.update(values)
