
//============================================================================
// Cell
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var SaveWidget = function (selector) {
        this.selector = selector;
        this.notebook_name_re = /[^/\\]+/
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };


    SaveWidget.prototype.style = function () {
        this.element.find('input#notebook_name').addClass('ui-widget ui-widget-content');
        this.element.find('button#save_notebook').button();
        var left_panel_width = $('div#left_panel').outerWidth();
        var left_panel_splitter_width = $('div#left_panel_splitter').outerWidth();
        $('span#save_widget').css({marginLeft:left_panel_width+left_panel_splitter_width});
    };


    SaveWidget.prototype.bind_events = function () {
        var that = this;
        this.element.find('button#save_notebook').click(function () {
            IPython.notebook.save_notebook();
        });

        $(window).bind('beforeunload', function () {
            var kill_kernel = $('#kill_kernel').prop('checked');
            IPython.notebook.save_notebook();
            if (kill_kernel) {
                IPython.notebook.kernel.kill();
                return "You are about to exit this notebook and kill the kernel.";
            } else {
                return "You are about the exit this notebook and leave the kernel running.";
            };
        });
    };


    SaveWidget.prototype.get_notebook_name = function () {
        return this.element.find('input#notebook_name').attr('value');
    }


    SaveWidget.prototype.set_notebook_name = function (nbname) {
        this.element.find('input#notebook_name').attr('value',nbname);
    }


    SaveWidget.prototype.get_notebook_id = function () {
        return this.element.find('span#notebook_id').text()
    };


    SaveWidget.prototype.update_url = function () {
        var notebook_id = this.get_notebook_id();
        if (notebook_id !== '') {
            window.history.replaceState({}, '', notebook_id);
        };
    };


    SaveWidget.prototype.test_notebook_name = function () {
        var nbname = this.get_notebook_name();
        if (this.notebook_name_re.test(nbname)) {
            return true;
        } else {
            var bad_name = $('<div/>');
            bad_name.html(
                "The notebook name you entered (" +
                nbname +
                ") is not valid. Notebook names can contain any characters except / and \\"
            );
            bad_name.dialog({title: 'Invalid name', modal: true});
            return false;
        };
    };


    SaveWidget.prototype.status_save = function () {
        this.element.find('span.ui-button-text').text('Save');
        this.element.find('button#save_notebook').button('enable');
    };    


    SaveWidget.prototype.status_saving = function () {
        this.element.find('span.ui-button-text').text('Saving');
        this.element.find('button#save_notebook').button('disable');
    };    


    SaveWidget.prototype.status_loading = function () {
        this.element.find('span.ui-button-text').text('Loading');
        this.element.find('button#save_notebook').button('disable');
    };    


    IPython.SaveWidget = SaveWidget;

    return IPython;

}(IPython));

