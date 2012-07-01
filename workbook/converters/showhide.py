from ..external import nbconvert as nbc

class HideData(nbc.ConverterNotebook):

    # prevent notebook name from changing
    def optional_header(self):
        s = \
"""{
 "metadata": {
 "name": "%(name)s"
 },
 "nbformat": 3,
 "worksheets": [
 {
 "cells": [""" % {'name':self.nb.metadata['name']}

        return s.split('\n')
    
    @nbc.DocInherit
    def render_code(self, cell):
        if is_workbook_cell(cell):
            cell.input = ''
        return nbc.ConverterNotebook.render_code(self, cell)

class MergeData(nbc.ConverterNotebook):

    def __init__(self, infile, outbase, local_nb):
        self.local_nb = local_nb
        # get all the workbook cells from local (server) copy of notebook
        local_wb_cells = []
        for ws in local_nb.worksheets:
            local_wb_cells.extend([ cell for cell in ws.cells if is_workbook_cell(cell) ] )
        self.local_wb_cells = local_wb_cells
        nbc.ConverterNotebook.__init__(self, infile, outbase)

    # prevent notebook name from changing
    def optional_header(self):
        s = \
"""{
 "metadata": {
 "name": "%(name)s"
 },
 "nbformat": 3,
 "worksheets": [
 {
 "cells": [""" % {'name':self.nb.metadata['name']}

        return s.split('\n')

    @nbc.DocInherit
    def render_code(self, active_cell):
        if is_workbook_cell(active_cell):
            # get all workbook cells in local copy that match given cell
            local_cells_match = [local_cell for local_cell in self.local_wb_cells \
                                     if local_cell.metadata.readonly.identifier == active_cell.metadata.readonly.identifier]
            # make sure there are exactly 1
            if len(local_cells_match) == 1:
                local_cell = local_cells_match[0]
                # make sure input and read-only metadata do not change
                active_cell.input = local_cell.input
                ro = local_cell.metadata['readonly']
                active_cell.metadata['readonly'] = ro

            else:
                raise Exception
        
        return nbc.ConverterNotebook.render_code(self, active_cell)

def is_workbook_cell(cell):
    return hasattr(cell.metadata, 'readonly') and hasattr(cell.metadata.readonly, 'owner') and \
        cell.metadata.readonly['owner']=='workbook' and hasattr(cell.metadata.readonly, 'identifier')
