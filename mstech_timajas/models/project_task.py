from odoo import models,fields,api,_
from datetime import timedelta, datetime
from odoo.exceptions import UserError

class ProjectTaskTimajas(models.Model):
    _inherit = "project.task"
    
    create_function = fields.Char(related='create_uid.function', readonly=True)
    state_payment_invoice = fields.Selection(related='sale_order_id.invoice_ids.payment_state',string="Estado de Pago Factura" ,readonly=True)  
    #--------------------------------------------------------------------------------------------------------------------------------
    task_picking = fields.One2many('stock.picking','picking_task', string="Herram.")
    om_mrp = fields.One2many('mrp.production','om_project',string="Ordenn de Manufactura")
    proj_mant = fields.One2many('maintenance.request','mant_project',string="Peticion de Mantenimiento")
    #--------------------------------------------------------------------------------------------------------------------------------
    task_eqip = fields.Many2one('maintenance.equipment', string="Tarea en equipos", compute='_compute_task_eqip')
    #--------------------------------------------------------------------------------------------------------------------------------
    @api.onchange('proj_mant')
    def _compute_task_eqip(self):
        for rec in self:
            rec.task_eqip = rec.proj_mant.equipment_id
	#-------------------------------------------------------------------------------------------------------------------------------
    @api.depends('sale_line_id.order_id.procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids')
    def obtener_manufacture_sale_order(self):
        for record in self:
            if record.sale_line_id.order_id:
                dic = record.sale_line_id.order_id.action_view_mrp_production()
                x_id = dic.get('res_id',dic.get('domain',[(False,False,False)])[0][2])
                if x_id:
                    self.env['mrp.production'].browse(x_id).write({'om_project' : record.id})
    #================================================================================================================================
    @api.onchange('om_mrp', 'sale_order_id')
    def onchange_origin_location(self):
        for record in self:
            manufacture = record.om_mrp
            if record.sale_order_id:
                sale_order = record.sale_order_id
                if manufacture.state == 'done':
                    sale_order_line = {
                        'order_id': sale_order.id,
                        'product_id': manufacture.product_id.id,
                        'price_unit': manufacture.product_id.list_price,
                        'product_uom_qty': manufacture.product_qty,
                        #'qty_delivered' : manufacture.product_qty,
                        'tax_id': manufacture.product_id.taxes_id,
                        'is_downpayment': False,
                        'discount': 0.0,
                    }
                    self.env['sale.order.line'].create(sale_order_line)
    #================================================================================================================================
class MrpProducction(models.Model):
    _inherit = "mrp.production"
    om_project = fields.Many2one('project.task', string="OM en Proyecto")
    
    @api.onchange('om_project', 'product_id')
    def onchange_origin_location(self):
        for record in self:
            if record.om_project:
                record.origin = record.om_project.name#+ " / " + record.om_project.sale_order_id.name
                #record.location_src_id = (20, 'EW/Stock')
                #record.location_dest_id = (20, 'EW/Stock')
    
class StockPickingTask(models.Model):
    _inherit = 'stock.picking'   
    picking_task = fields.Many2one('project.task', string="tarea en movimiento")
    
    @api.model
    def create(self, vals):
        defaults = self.default_get(['name', 'picking_type_id'])
        picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))             
        if self.picking_task:
            if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
                vals['name'] = picking_type.sequence_id.next_by_id()
        res = super(StockPickingTask,self).create(vals)      
        return res
    
    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        for record in self:
            if record.picking_task:
                record.picking_type_id = (5, 'San Francisco: Internal Transfers')
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for record in self:
            if record.picking_task:
                record.partner_id = record.picking_task.partner_id
        parti = None
        if hasattr(super(), 'onchange_partner_id'):
            parti = super().onchange_partner_id()
        return parti
    
    @api.depends('state', 'move_lines', 'move_lines.state', 'move_lines.package_level_id', 'move_lines.move_line_ids.package_level_id')
    def _compute_move_without_package(self):
        for record in self:
            if record.picking_task:
                movimi = record.move_ids_without_package       
                pass
        mov_he = super()._compute_move_without_package()
        return mov_he
    
    def validate_directo(self):
        for record in self:
            record.action_confirm()
            record.action_assign()
            if record.action_assign() == True:
                record.button_validate()
                #record.button_validate()
        return True
