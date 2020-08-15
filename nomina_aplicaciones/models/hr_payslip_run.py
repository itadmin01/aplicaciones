# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging
_logger = logging.getLogger(__name__)

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    proyeccion = fields.Boolean(string='Proyeccion')
