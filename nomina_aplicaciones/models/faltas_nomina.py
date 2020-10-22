# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class FaltasNomina(models.Model):
    _inherit = 'faltas.nomina'
    
    tipo_de_falta = fields.Selection(selection_add=[('incapacidad', 'Incapacidad')])
    