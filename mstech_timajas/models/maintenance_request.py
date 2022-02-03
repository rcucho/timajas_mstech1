from odoo import models,fields,api,_
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta, datetime
from odoo.exceptions import UserError

class MaintenanceRequestTimajas(models.Model):
    _inherit = "maintenance.request"
    #-------------------------------------------------------------------------------------------------------------------
    mant_project = fields.Many2one('project.task', string="Project")
    #-------------------------------------------------------------------------------------------------------------------
    @api.onchange('stage_id')
    def _compute_mant_project(self):
        for record in self:
            if record.stage_id.id == 2:
                record.mant_project = self.env['project.task'].create({
                    'name': record.name,
                    'user_ids' : record.user_id,
                    'project_id' : 17,
                })

class MaintenanceEquipment2(models.Model):
    _inherit = "maintenance.equipment"
    #-------------------------------------------------------------------------------------------------------------------
    eqip_product = fields.Many2one('product.product', string="Producto")
    #-------------------------------------------------------------------------------------------------------------------
    eqip_task = fields.One2many('project.task','task_eqip', string="Equipo en Tareas")
    task_count = fields.Integer(compute='_compute_eqip_task', string="Project Count")
    stock_eq_cont = fields.Integer(compute='_compute_stock_eq_count', string="Inventario C")
    stock_eq = fields.One2many(string="Mov de Repuestos", related='eqip_task.task_picking.move_ids_without_package')
    #-------------------------------------------------------------------------------------------------------------------
    mant_lote =fields.Many2one('stock.production.lot',string="Producto/Serie")
    #-------------------------------------------------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        equipment = super().create(vals)
        list_name = self.env['product.product'].search([]).mapped('name')
        #list_name1 = [x.lower() for x in list_name]
        for record in equipment:
            lst_word = record.name.split(' ')
            #lst_word1 = [x.lower() for x in lst_word]
            if lst_word[0] in list_name:
                record.eqip_product = self.env['product.product'].search([('name','=',lst_word[0])])
            else:
                record.eqip_product = self.env['product.product'].create({
                    'name': record.name,
                    'detailed_type' : 'product',
                    'tracking' : 'serial',
                })
                
                if record.serial_no and not record.mant_lote:
                    record.mant_lote = self.env['stock.production.lot'].create({
                        'name': record.serial_no,
                        'company_id' : record.company_id.id,
                        'product_id' : record.eqip_product.id,
                    })
        return equipment
    
    def write(self, vals):
        equipment = super().write(vals)
        for record in self:
            if record.serial_no and not record.mant_lote:
                if record.eqip_product.id:
                    record.mant_lote = self.env['stock.production.lot'].create({
                        'name': record.serial_no,
                        'company_id' : record.company_id.id,
                        'product_id' : record.eqip_product.id,
                    })
        return equipment
    #--------------------------------------------------------------------------------------------------------------------
    @api.onchange('maintenance_ids')
    def _compute_eqip_task(self):
        for rec in self:
            #taks2 = env['project.task'].task_eqip.search([('name','=',rec.name)])
            #task3 = self.env['project.task'].search([('task_picking.move_ids_without_package.product_id.name','=',rec.name)])
            #
            tasks = rec.maintenance_ids.mant_project
            rec.eqip_task = tasks
            rec.task_count = len(tasks)
    
    @api.onchange('eqip_task')
    def _compute_stock_eq_count(self):
        for rec in self:
            qnt_mov = 0
            proj_task = rec.eqip_task
            for r in proj_task:
                pick = r.task_picking
                move_pro = pick.move_ids_without_package
                for m in move_pro:
                    qnt_mov = qnt_mov + m.quantity_done
            rec.stock_eq_cont = qnt_mov 
    #------------------------------------------------------------------------------------------
    def action_view_task3(self):
        self.ensure_one()
        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id

        action = {'type': 'ir.actions.act_window_close'}
        task_projects = self.eqip_task.mapped('project_id')
        if len(task_projects) == 1 and len(self.eqip_task) > 1:
            action = self.with_context(active_id=task_projects.id).env['ir.actions.actions']._for_xml_id(
                'project.act_project_project_2_project_task_all')
            action['domain'] = [('id', 'in', self.eqip_task.ids)]
            if action.get('context'):
                eval_context = self.env['ir.actions.actions']._get_eval_context()
                eval_context.update({'active_id': task_projects.id})
                action_context = safe_eval(action['context'], eval_context)
                action_context.update(eval_context)
                action['context'] = action_context
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
            action['context'] = {}
            if len(self.eqip_task) > 1:
                action['views'] = [[False, 'kanban'], [list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'calendar'], [False, 'pivot']]
            elif len(self.eqip_task) == 1:
                action['views'] = [(form_view_id, 'form')]
                action['res_id'] = self.eqip_task.id
        action.setdefault('context', {})
        return action
    #=====================================================================================
    def action_view_stock_move_lines2(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_line_action")
        action['domain'] = [('picking_id', 'in', self.eqip_task.task_picking.ids)]
        return action
    #===================================================================================== 
class ProductTemplate(models.Model):
    _inherit = "product.product"
    #-------------------------------------------------------------------------------------------------------------------
    product_eqip = fields.One2many('maintenance.equipment', 'eqip_product', string="Equipamento de Mantenimiento")
    stock_count = fields.Integer(compute='_compute_stock_count', string="Repuestos Usados en Mantenimiento", store= False)
    #-------------------------------------------------------------------------------------------------------------------
    tasks_mant_ids = fields.Many2many('project.task', compute="_compute_tasks_ids", string='Projects')
    task_count = fields.Integer(compute='_compute_tasks_ids', string="Project Count")
    #-------------------------------------------------------------------------------------------------------------------    
    @api.depends('stock_move_ids')
    def _compute_stock_count(self):
        for record in self:
            qnt_pro = 0
            proj_task = record.tasks_mant_ids
            for r in proj_task:
                pick = r.task_picking
                move_pro = pick.move_ids_without_package
                for m in move_pro:
                    qnt_pro = qnt_pro + m.quantity_done
            record.stock_count = qnt_pro

    @api.depends('product_eqip')
    def _compute_tasks_ids(self):
        for rec in self:
            tasks = rec.product_eqip.mapped('maintenance_ids.mant_project')
            rec.tasks_mant_ids = tasks
            rec.task_count = len(tasks)
    
    def action_view_tasks_mant_ids(self):
        self.ensure_one()
        view_form_id = self.env.ref('project.edit_project').id
        view_kanban_id = self.env.ref('project.view_project_kanban').id
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.tasks_mant_ids.ids)],
            'view_mode': 'kanban,form',
            'name': _('Projects'),
            'res_model': 'project.task',
        }
        if len(self.tasks_mant_ids) == 1:
            action.update({'views': [(view_form_id, 'form')], 'res_id': self.tasks_mant_ids.id})
        else:
            action['views'] = [(view_kanban_id, 'kanban'), (view_form_id, 'form')]
        return action

    def action_view_task2(self):
        self.ensure_one()
        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id

        action = {'type': 'ir.actions.act_window_close'}
        task_projects = self.tasks_mant_ids.mapped('project_id')
        if len(task_projects) == 1 and len(self.tasks_mant_ids) > 1:
            action = self.with_context(active_id=task_projects.id).env['ir.actions.actions']._for_xml_id(
                'project.act_project_project_2_project_task_all')
            action['domain'] = [('id', 'in', self.tasks_mant_ids.ids)]
            if action.get('context'):
                eval_context = self.env['ir.actions.actions']._get_eval_context()
                eval_context.update({'active_id': task_projects.id})
                action_context = safe_eval(action['context'], eval_context)
                action_context.update(eval_context)
                action['context'] = action_context
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
            action['context'] = {}
            if len(self.tasks_mant_ids) > 1:
                action['views'] = [[False, 'kanban'], [list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'calendar'], [False, 'pivot']]
            elif len(self.tasks_mant_ids) == 1:
                action['views'] = [(form_view_id, 'form')]
                action['res_id'] = self.tasks_mant_ids.id
        action.setdefault('context', {})
        return action
                
class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    product_eqip_temp = fields.One2many(string="Equipamento de Mantenimiento", related='product_variant_id.product_eqip')
    project_count_temp = fields.Integer(string="Task Count", related='product_variant_id.task_count')
    
class MaintenanceEquipment2(models.Model):
    _inherit = "stock.production.lot"
    lote_mant = fields.One2many('maintenance.equipment','mant_lote',string="Lote de Equipo")
