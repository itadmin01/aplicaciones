# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'
    
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Regla Salarial')
    
    @api.onchange('salary_rule_id')
    def onchange_salary_rule(self):
        salary_rule = self.salary_rule_id
        if salary_rule:
           self.name = salary_rule.name
           self.code = salary_rule.code
           
           