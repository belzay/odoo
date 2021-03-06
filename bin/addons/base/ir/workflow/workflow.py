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

from osv import fields, osv
from tools import graph
import netsvc

class workflow(osv.osv):
    _name = "workflow"
    _table = "wkf"
  #  _log_access = False
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'osv': fields.char('Resource Object', size=64, required=True,select=True),
        'on_create': fields.boolean('On Create', select=True),
        'activities': fields.one2many('workflow.activity', 'wkf_id', 'Activities'),
    }
    _defaults = {
        'on_create': lambda *a: True
    }

    def write(self, cr, user, ids, vals, context=None):
        if not context:
            context={}
        wf_service = netsvc.LocalService("workflow")
        wf_service.clear_cache(cr, user)
        return super(workflow, self).write(cr, user, ids, vals, context=context)

    #
    # scale =  (vertical-distance, horizontal-distance, min-node-width(optional), min-node-height(optional), margin(default=20))
    #


    def graph_get(self, cr, uid, id, scale, context={}):

        nodes= []
        nodes_name = []
        transitions = []
        start = []
        tres = {}
        no_ancester = []
        workflow = self.browse(cr, uid, id, context)
        for a in workflow.activities:
            nodes_name.append((a.id,a.name))
            nodes.append(a.id)
            if a.flow_start:
                start.append(a.id)
            else:
                if not a.in_transitions:
                    no_ancester.append(a.id)

            for t in a.out_transitions:
                transitions.append((a.id, t.act_to.id))
                tres[t.id] = (a.id, t.act_to.id)


        g  = graph(nodes, transitions, no_ancester)
        g.process(start)
        g.scale(*scale)
        result = g.result_get()
        results = {}

        for node in nodes_name:
            results[str(node[0])] = result[node[0]]
            results[str(node[0])]['name'] = node[1]

        return {'nodes': results, 'transitions': tres}


    def create(self, cr, user, vals, context=None):
        if not context:
            context={}
        wf_service = netsvc.LocalService("workflow")
        wf_service.clear_cache(cr, user)
        return super(workflow, self).create(cr, user, vals, context=context)
workflow()

class wkf_activity(osv.osv):
    _name = "workflow.activity"
    _table = "wkf_activity"
   # _log_access = False
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'wkf_id': fields.many2one('workflow', 'Workflow', required=True, select=True, ondelete='cascade'),
        'split_mode': fields.selection([('XOR', 'Xor'), ('OR','Or'), ('AND','And')], 'Split Mode', size=3, required=True),
        'join_mode': fields.selection([('XOR', 'Xor'), ('AND', 'And')], 'Join Mode', size=3, required=True),
        'kind': fields.selection([('dummy', 'Dummy'), ('function', 'Function'), ('subflow', 'Subflow'), ('stopall', 'Stop All')], 'Kind', size=64, required=True),
        'action': fields.text('Python Action'),
        'action_id': fields.many2one('ir.actions.server', 'Server Action', ondelete='set null'),
        'flow_start': fields.boolean('Flow Start'),
        'flow_stop': fields.boolean('Flow Stop'),
        'subflow_id': fields.many2one('workflow', 'Subflow'),
        'signal_send': fields.char('Signal (subflow.*)', size=32),
        'out_transitions': fields.one2many('workflow.transition', 'act_from', 'Outgoing Transitions'),
        'in_transitions': fields.one2many('workflow.transition', 'act_to', 'Incoming Transitions'),
    }
    _defaults = {
        'kind': lambda *a: 'dummy',
        'join_mode': lambda *a: 'XOR',
        'split_mode': lambda *a: 'XOR',
    }
wkf_activity()

class wkf_transition(osv.osv):
    _table = "wkf_transition"
    _name = "workflow.transition"
   # _log_access = False
    _rec_name = 'signal'
    _columns = {
        'trigger_model': fields.char('Trigger Object', size=128),
        'trigger_expr_id': fields.char('Trigger Expression', size=128),
        'signal': fields.char('Signal (button Name)', size=64),
        'role_id': fields.many2one('res.roles', 'Role Required'),
        'condition': fields.char('Condition', required=True, size=128),
        'act_from': fields.many2one('workflow.activity', 'Source Activity', required=True, select=True, ondelete='cascade'),
        'act_to': fields.many2one('workflow.activity', 'Destination Activity', required=True, select=True, ondelete='cascade'),
    }
    _defaults = {
        'condition': lambda *a: 'True',
    }
wkf_transition()

class wkf_instance(osv.osv):
    _table = "wkf_instance"
    _name = "workflow.instance"
    _rec_name = 'res_type'
    _log_access = False
    _columns = {
        'wkf_id': fields.many2one('workflow', 'Workflow', ondelete='cascade', select=True),
        'uid': fields.integer('User ID'),
        'res_id': fields.integer('Resource ID', select=True),
        'res_type': fields.char('Resource Object', size=64, select=True),
        'state': fields.char('State', size=32, select=True),
    }
    def _auto_init(self, cr, context={}):
        super(wkf_instance, self)._auto_init(cr, context)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'wkf_instance_res_id_res_type_state_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX wkf_instance_res_id_res_type_state_index ON wkf_instance (res_id, res_type, state)')
            cr.commit()
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'wkf_instance_res_id_wkf_id_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX wkf_instance_res_id_wkf_id_index ON wkf_instance (res_id, wkf_id)')
            cr.commit()

wkf_instance()

class wkf_workitem(osv.osv):
    _table = "wkf_workitem"
    _name = "workflow.workitem"
    _log_access = False
    _rec_name = 'state'
    _columns = {
        'act_id': fields.many2one('workflow.activity', 'Activity', required=True, ondelete="cascade", select=True),
        'subflow_id': fields.many2one('workflow.instance', 'Subflow', ondelete="cascade", select=True),
        'inst_id': fields.many2one('workflow.instance', 'Instance', required=True, ondelete="cascade", select=True),
        'state': fields.char('State', size=64, select=True),
    }
wkf_workitem()

class wkf_triggers(osv.osv):
    _table = "wkf_triggers"
    _name = "workflow.triggers"
    _log_access = False
    _columns = {
        'res_id': fields.integer('Resource ID', size=128),
        'model': fields.char('Object', size=128),
        'instance_id': fields.many2one('workflow.instance', 'Destination Instance', ondelete="cascade"),
        'workitem_id': fields.many2one('workflow.workitem', 'Workitem', required=True, ondelete="cascade"),
    }
    def _auto_init(self, cr, context={}):
        super(wkf_triggers, self)._auto_init(cr, context)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'wkf_triggers_res_id_model_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX wkf_triggers_res_id_model_index ON wkf_triggers (res_id, model)')
            cr.commit()
wkf_triggers()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

