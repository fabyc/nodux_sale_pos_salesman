# This file is part of the sale_pos_salesman module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .sale import *

def register():
    Pool.register(
        PrintSalesmanReportStart,
        module='nodux_sale_pos_salesman', type_='model')
    Pool.register(
        SalesmanReport,
        module='nodux_sale_pos_salesman', type_='report')
    Pool.register(
        PrintSalesmanReport,
        module='nodux_sale_pos_salesman', type_='wizard')
