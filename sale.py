#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from decimal import Decimal
from datetime import date
import operator
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.report import Report
from trytond.pyson import Eval, PYSONEncoder
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.modules.company import CompanyReport
import pytz
from datetime import datetime,timedelta
import time

__all__ = ['PrintSalesmanReportStart','PrintSalesmanReport', 'SalesmanReport']

__metaclass__ = PoolMeta

class PrintSalesmanReportStart(ModelView):
    'Print Sale Report Start'
    __name__ = 'nodux_sale_pos_salesman.print_sale_report.start'
    company = fields.Many2One('company.company', 'Company', required=True)
    date = fields.Date("Date", help="Seleccione la fecha de la cual desea imprimir el reporte")
    date_end = fields.Date("Date End", help="Seleccione la fecha limite para imprimir el reporte")
    employee = fields.Many2One('company.employee', 'Salesman',
        domain=[
            ('company', '=', Eval('company', -1)),
            ],
        depends=['state', 'company'])
    paid = fields.Boolean('Paid Sales', help="Reporte de ventas que ya han sido pagadas")

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_date():
        date = Pool().get('ir.date')
        date = date.today()
        return date

    @staticmethod
    def default_date_end():
        date = Pool().get('ir.date')
        date = date.today()
        return date

class PrintSalesmanReport(Wizard):
    'Print Sale Report'
    __name__ = 'nodux_sale_pos_salesman.print_sale_report'
    start = StateView('nodux_sale_pos_salesman.print_sale_report.start',
        'nodux_sale_pos_salesman.print_sale_report_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Print', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateAction('nodux_sale_pos_salesman.report_sale_report')

    def do_print_(self, action):
        if self.start.employee:
            data = {
                'company': self.start.company.id,
                'date' : self.start.date,
                'date_end' : self.start.date_end,
                'employee': self.start.employee.id,
                'paid': self.start.paid
                }
        else:
            data = {
                'company': self.start.company.id,
                'date' : self.start.date,
                'employee' : None,
                'date_end' : self.start.date_end,
                'paid': self.start.paid
                }
        return action, data

    def transition_print_(self):
        return 'end'

class SalesmanReport(Report):
    __name__ = 'nodux_sale_pos_salesman.sale_report'

    @classmethod
    def parse(cls, report, objects, data, localcontext):
        pool = Pool()
        User = pool.get('res.user')
        user = User(Transaction().user)
        Date = pool.get('ir.date')
        Sale = pool.get('sale.sale')
        Employee = pool.get('company.employee')
        Company = pool.get('company.company')
        date = data['date']
        date_end = data['date_end']
        paid = data['paid']
        if data['employee']:
            employee = Employee(data['employee'])
        else:
            employee = None
        company = Company(data['company'])
        total_iva =  Decimal(0.0)
        total_base =  Decimal(0.0)
        total_ventas =  Decimal(0.0)
        if company.timezone:
            timezone = pytz.timezone(company.timezone)
            dt = datetime.now()
            hora = datetime.astimezone(dt.replace(tzinfo=pytz.utc), timezone)
        if paid == True:
            if employee:
                if  date_end:
                    sales = Sale.search([('employee', '=', employee), ('sale_date', '>=', date), ('sale_date', '<=', date_end),('state', '=', 'done')])
                else:
                    sales = Sale.search([('employee', '=', employee), ('sale_date', '=', date), ('state', '=', 'done')])
            else:
                if  date_end:
                    sales = Sale.search([('sale_date', '>=', date), ('sale_date', '<=', date_end),('state', '=', 'done')])
                else:
                    sales = Sale.search([('sale_date', '=', date),('state', '=', 'done')])

        else:
            if employee:
                if  date_end:
                    sales = Sale.search([('employee', '=', employee), ('sale_date', '>=', date), ('sale_date', '<=', date_end),('state', '!=', 'quotation'), ('state', '!=', 'draft')])
                else:
                    sales = Sale.search([('employee', '=', employee), ('sale_date', '=', date),('state', '!=', 'quotation'), ('state', '!=', 'draft')])
            else:
                if  date_end:
                    sales = Sale.search([('sale_date', '>=', date), ('sale_date', '<=', date_end),('state', '!=', 'quotation'), ('state', '!=', 'draft')])
                else:
                    sales = Sale.search([('sale_date', '=', date),('state', '!=', 'quotation'), ('state', '!=', 'draft')])

        lines = {}
        sale_salesman = []

        for s in sales:
            lines = {}
            party = s.party
            base = s.untaxed_amount_cache
            iva = s.tax_amount_cache
            total = s.total_amount_cache
            total_iva += iva
            total_base += base
            total_ventas += total
            lines['date'] = s.sale_date
            lines['party'] = party
            lines['base'] = base
            lines['iva'] = iva
            lines['total'] = total

            sale_salesman.append(lines)

        localcontext['employee'] = employee
        localcontext['company'] = company
        localcontext['fecha'] = date.strftime('%d/%m/%Y')
        localcontext['fin'] = date_end.strftime('%d/%m/%Y')
        localcontext['total_iva'] = total_iva
        localcontext['total_base'] = total_base
        localcontext['total_ventas']= total_ventas
        localcontext['sale_salesman'] = sale_salesman
        localcontext['hora'] = hora.strftime('%H:%M:%S')
        localcontext['fecha_im'] = hora.strftime('%d/%m/%Y')

        return super(SalesmanReport, cls).parse(report, objects, data, localcontext)
