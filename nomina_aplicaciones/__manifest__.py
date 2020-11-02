# -*- coding: utf-8 -*-

{
    'name': 'Modificaciones para nómina de Mitzu',
    'summary': 'Modificaciones al cálculo del SDI, agregar función para estimar nomins de gratificacion y 2da quincena de diciembre',
    'description': '''
    Modificaciones del cálculo del SDI
    ''',
    'author': 'IT Admin',
    'version': '13.08',
    'category': 'Employees',
    'depends': [
        'om_hr_payroll', 'nomina_cfdi_ee', 'nomina_cfdi_extras_ee',
    ],
    'data': [
        'views/hr_payroll_payslip_view.xml',
        'views/hr_payslip_input_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
