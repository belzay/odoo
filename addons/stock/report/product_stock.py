# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from mx import DateTime

import osv
import time
from report.interface import report_int
from report.render import render

import stock_graph
import pooler
import StringIO

class external_pdf(render):
    def __init__(self, pdf):
        render.__init__(self)
        self.pdf = pdf
        self.output_type='pdf'
    
    def _render(self):
        return self.pdf


class report_stock(report_int):
    def create(self, cr, uid, ids, datas, context={}):
        product_ids = ids
        if 'location_id' in context:
            location_id = context['location_id']
        else:
            warehouse_id = pooler.get_pool(cr.dbname).get('stock.warehouse').search(cr, uid, [])[0]
            location_id = pooler.get_pool(cr.dbname).get('stock.warehouse').browse(cr, uid, warehouse_id).lot_stock_id.id

        loc_ids = pooler.get_pool(cr.dbname).get('stock.location').search(cr, uid, [('location_id','child_of',[location_id])])

        now = time.strftime('%Y-%m-%d')
        dt_from = now
        dt_to = now

        names = dict(pooler.get_pool(cr.dbname).get('product.product').name_get(cr, uid, product_ids))
        for name in names:
            names[name] = names[name].encode('utf8')
        products = {}
        prods = pooler.get_pool(cr.dbname).get('stock.location')._product_all_get(cr, uid, location_id, product_ids)

        for p in prods:
            products[p] = [(now,prods[p])]
            prods[p] = 0

        if not loc_ids or not product_ids:
            return (False, 'pdf')

        loc_ids_s = ",".join(['%s']*len(loc_ids))
        prod_ids_s = ",".join(['%s']*len(product_ids))

        cr.execute("select sum(r.product_qty * u.factor), r.date_planned, r.product_id "
                   "from stock_move r left join product_uom u on (r.product_uom=u.id) "
                   "where state in ('confirmed','assigned','waiting') "
                   "and location_id in (%s) "
                   "and product_id in (%s) "
                   "group by date_planned,product_id" % (loc_ids_s, prod_ids_s),
                   loc_ids + product_ids)

        for (qty, dt, prod_id) in cr.fetchall():
            if dt<=dt_from:
                dt= (DateTime.now() + DateTime.RelativeDateTime(days=1)).strftime('%Y-%m-%d')
            else:
                dt = dt[:10]
            products.setdefault(prod_id, [])
            products[prod_id].append((dt,-qty))

        cr.execute("select sum(r.product_qty * u.factor), r.date_planned, r.product_id "
                   "from stock_move r left join product_uom u on (r.product_uom=u.id) "
                   "where state in ('confirmed','assigned','waiting') "
                   "and location_dest_id in (%s) "
                   "and product_id in (%s) "
                   "group by date_planned,product_id" % (loc_ids_s, prod_ids_s),
                   loc_ids + product_ids)

        for (qty, dt, prod_id) in cr.fetchall():
            if dt<=dt_from:
                dt= (DateTime.now() + DateTime.RelativeDateTime(days=1)).strftime('%Y-%m-%d')
            else:
                dt = dt[:10]
            products.setdefault(prod_id, [])
            products[prod_id].append((dt,qty))

        dt = dt_from
        qty = 0

        io = StringIO.StringIO()
        gt = stock_graph.stock_graph(io)
        for prod_id in products:
            gt.add(prod_id, names.get(prod_id, 'Unknown'), products[prod_id])
        gt.draw()
        gt.close()
        self.obj = external_pdf(io.getvalue())
        self.obj.render()
        return (self.obj.pdf, 'pdf')
report_stock('report.stock.product.history')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

