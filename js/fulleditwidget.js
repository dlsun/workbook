//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// MenuBar
//============================================================================

var IPython = (function (IPython) {

    var FullEditWidget = function (selector) {
        this.selector = selector;
        this.opened = false;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };


    FullEditWidget.prototype.style = function () {
        var that = this;
        this.element.find('#close_fulledit').button().on('click', function (){
            that.close();
        })
        // this.element.find('#fulledit_widget').addClass('ui-widget ui-widget-content');
        this.element.find('#fulledit_header').addClass('ui-widget ui-widget-header');
        this.element.find('#fulledit_editor').addClass('ui-widget ui-widget-content');
        this.ace_editor = ace.edit("fulledit_editor");
        this.ace_editor.setTheme("ace/theme/textmate");
        var PythonMode = require("ace/mode/python").Mode;
        this.ace_editor.getSession().setMode(new PythonMode());
        this.ace_editor.getSession().setTabSize(4);
        this.ace_editor.getSession().setUseSoftTabs(true);
        this.ace_editor.setHighlightActiveLine(false);
    };


    FullEditWidget.prototype.bind_events = function () {

    };


    FullEditWidget.prototype.open = function () {
        var cell = IPython.notebook.selected_cell();
        if (!this.opened && cell instanceof IPython.CodeCell) {
            $('#fulledit_widget').show();
            $('#main_app').hide();
            $('#menubar').hide();
            $('body').css({overflow : 'auto'});
            var code = cell.get_code();
            this.ace_editor.getSession().setValue(code);
            this.ace_editor.focus();
            this.opened = true;
        };
    };


    FullEditWidget.prototype.close = function () {
        if (this.opened) {
            $('#fulledit_widget').hide();
            $('#main_app').show();
            $('#menubar').show();
            $('body').css({overflow : 'hidden'});
            var code = this.ace_editor.getSession().getValue();
            var cell = IPython.notebook.selected_cell();
            cell.set_code(code);
            cell.select();
            this.opened = false;
        };
    };


    FullEditWidget.prototype.toggle = function () {
        if (this.opened) {
            this.close();
        } else {
            this.open();
        };
    };


    IPython.FullEditWidget = FullEditWidget;

    return IPython;

}(IPython));
