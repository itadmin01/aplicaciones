# -*- coding: utf-8 -*-

{
    'name': 'Modificaciones para nómina de Mitzu',
    'summary': 'Modificaciones al cálculo del SDI, agregar función para estimar nomins de gratificacion y 2da quincena de diciembre',
    'description': '''
    Modificaciones del cálculo del SDI
    ''',
    'author': 'IT Admin',
    'version': '13.03',
    'category': 'Employees',
    'depends': [
        'nomina_cfdi_ee',
    ],
    'data': [
        'views/hr_payroll_payslip_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
